#!/usr/bin/env python3
"""
Script de prueba de la integración Odoo (108) -> FET (104).

Objetivo: comprobar, desde la máquina de Odoo, que se puede enviar un archivo
.fet al servicio FET, esperar a que genere el horario y recoger el XML.

NO forma parte de Odoo: es solo una prueba de conexión y del flujo completo.

Uso:
    python3 test_fet_api.py horario.fet
    python3 test_fet_api.py horario.fet --host 192.168.1.104 --timelimit 60

Requisitos: la librería 'requests' (Odoo ya la incluye).
"""

import argparse
import sys
import time

try:
    import requests
except ImportError:
    sys.exit("Falta la librería 'requests'. Instálala con: pip3 install requests")


def main() -> int:
    parser = argparse.ArgumentParser(description="Prueba del servicio FET desde Odoo")
    parser.add_argument("fet_file", help="Ruta al archivo .fet de entrada")
    parser.add_argument("--host", default="192.168.1.104", help="IP del servicio FET (máquina 104)")
    parser.add_argument("--port", type=int, default=8000, help="Puerto del servicio FET")
    parser.add_argument("--timelimit", type=int, default=60,
                        help="Límite de tiempo de generación en segundos")
    parser.add_argument("--output", default="activities_timetable.xml",
                        help="Dónde guardar el XML resultante")
    parser.add_argument("--poll", type=float, default=2.0,
                        help="Cada cuántos segundos preguntar si está listo")
    args = parser.parse_args()

    base = f"http://{args.host}:{args.port}"

    # --- Paso 0: comprobar que el servicio está vivo -------------------------
    print(f"[0] Comprobando que el servicio responde en {base} ...")
    try:
        r = requests.get(f"{base}/health", timeout=10)
        r.raise_for_status()
        print(f"    OK -> {r.json()}")
    except requests.RequestException as exc:
        print(f"    ERROR: no se puede contactar con el servicio FET: {exc}")
        print("    Revisa: ¿está levantado el contenedor? ¿abre el cortafuegos el puerto?")
        return 1

    # --- Paso 1: enviar el .fet ---------------------------------------------
    print(f"[1] Enviando '{args.fet_file}' ...")
    try:
        with open(args.fet_file, "rb") as fh:
            r = requests.post(
                f"{base}/timetable",
                files={"file": (args.fet_file.split("/")[-1], fh)},
                data={"timelimitseconds": args.timelimit},
                timeout=30,
            )
    except FileNotFoundError:
        print(f"    ERROR: no se encuentra el archivo '{args.fet_file}'")
        return 1
    except requests.RequestException as exc:
        print(f"    ERROR al enviar: {exc}")
        return 1

    if r.status_code != 202:
        print(f"    ERROR: respuesta inesperada ({r.status_code}): {r.text}")
        return 1
    job_id = r.json()["job_id"]
    print(f"    OK -> ticket (job_id) = {job_id}")

    # --- Paso 2: esperar a que termine --------------------------------------
    print("[2] Esperando a que FET genere el horario ...")
    while True:
        time.sleep(args.poll)
        try:
            r = requests.get(f"{base}/timetable/{job_id}", timeout=10)
            r.raise_for_status()
        except requests.RequestException as exc:
            print(f"    ERROR al consultar estado: {exc}")
            return 1
        estado = r.json()["status"]
        print(f"    estado: {estado}")
        if estado == "done":
            break
        if estado == "error":
            print(f"    ERROR de FET: {r.json().get('message')}")
            return 1

    # --- Paso 3: recoger el XML ---------------------------------------------
    print("[3] Descargando el horario generado ...")
    try:
        r = requests.get(f"{base}/timetable/{job_id}/result", timeout=30)
        r.raise_for_status()
    except requests.RequestException as exc:
        print(f"    ERROR al descargar: {exc}")
        return 1

    with open(args.output, "wb") as fh:
        fh.write(r.content)
    n_act = r.text.count("<Activity>")
    print(f"    OK -> guardado en '{args.output}' ({len(r.content)} bytes, {n_act} actividades)")
    print("\n¡Prueba completada con éxito! La conexión 108 -> 104 funciona.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
