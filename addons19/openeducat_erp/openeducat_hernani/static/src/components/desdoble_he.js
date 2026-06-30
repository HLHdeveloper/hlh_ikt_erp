/** @odoo-module */
import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

// Apartado DESDOBLE_HE: gestión de las copias de módulos por desdoble (DESDO_)
// y eleanitza (HE_). Reutiliza los RPC de op.faculty ya usados en Perfilazioak
// (selectores mintegi→zikloa→taldea + toggle_perfilazio_kopia + info/horas de
// desdoble). El objetivo es separar esta gestión de Perfilazioak, que queda
// solo para ver/asignar módulos.
class DesdobleHe extends Component {
    static template = "openeducat_hernani.DesdobleHe";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.state = useState({
            mintegiak: [],
            zikloak: [],
            batches: [],
            selectedMintegi: null,
            selectedZikloa: null,
            selectedBatch: null,

            // Resumen Eleanitza / Desdobleak del mintegi (igual que Perfilazioak)
            eleanitzaLaburpena: {
                eleanitza: { total: 0, pending: 0 },
                desdoblea: { total: 0, pending: 0 },
                errefortzuak: { total: 0, pending: 0 },
            },
            // Listas de módulos copia del mintegi (HE_, DESDO_ y ERREF_)
            eleanitzaModuluak: { eleanitza: [], desdoblea: [], errefortzuak: [] },
            // Reparto por zikloa→taldea (tablas de gestión). Cargado del servidor.
            kopiaBanaketa: [],
            // Modo de errefortzu del mintegi: 'poltsan' / 'taldean' / 'mix'.
            errefortzuMota: 'poltsan',
            // Reparto del total (solo MIX): horas a POLTSAN y a módulos.
            errefortzuPoltsan: 0,
            errefortzuModulu: 0,

            // Modo activo (mutuamente excluyente): '' | 'eleanitza' |
            // 'desdoblea' | 'errefortzuak'. Lo elige el desplegable "Mota".
            mota: '',
            zikloModuluak: [],
            selectedKopiak: {},
            // Horas de desdoble por módulo (clave = id del módulo origen).
            desdoOrduak: {},
            // Tope total de horas de desdoble del grupo y consumo.
            desdoInfo: { total: 0, used: 0, remaining: 0 },

            loading: false,
        });
        onWillStart(() => this._loadMintegiak());
    }

    async _loadMintegiak() {
        this.state.mintegiak = await this.orm.call("op.faculty", "get_perfilazio_mintegiak", []);
    }

    // ── Selectores en cascada Mintegia → Zikloa → Taldea ─────────────
    async onMintegiChange(ev) {
        const id = parseInt(ev.target.value) || null;
        this.state.selectedMintegi = this.state.mintegiak.find(m => m.id === id) || null;
        this.state.selectedZikloa = null;
        this.state.selectedBatch = null;
        this.state.zikloak = [];
        this.state.batches = [];
        this._resetKopiak();
        this._resetEleanitzaLaburpena();
        if (!id) return;
        this.state.loading = true;
        const [zikloak, eleanitza, eleanitzaMod, banaketa] = await Promise.all([
            this.orm.call("op.faculty", "get_perfilazio_zikloak", [id]),
            this.orm.call("op.faculty", "get_perfilazio_eleanitza_laburpena", [id]),
            this.orm.call("op.faculty", "get_perfilazio_eleanitza_moduluak", [id]),
            this.orm.call("op.faculty", "get_perfilazio_kopia_banaketa", [id]),
        ]);
        this.state.zikloak = zikloak;
        this.state.eleanitzaLaburpena = eleanitza;
        this.state.eleanitzaModuluak = eleanitzaMod;
        this.state.kopiaBanaketa = banaketa;
        this._applyErrefLaburpena(eleanitza);
        this.state.loading = false;
    }

    _resetEleanitzaLaburpena() {
        this.state.eleanitzaLaburpena = {
            eleanitza: { total: 0, pending: 0 },
            desdoblea: { total: 0, pending: 0 },
            errefortzuak: { total: 0, pending: 0 },
        };
        this.state.eleanitzaModuluak = { eleanitza: [], desdoblea: [], errefortzuak: [] };
        this.state.kopiaBanaketa = [];
    }

    // GUZTIRA de la tabla Eleanitza / Desdobleak / Errefortzuak.
    eleanitzaGuztira(field) {
        const e = this.state.eleanitzaLaburpena;
        return Math.round((((e.eleanitza[field] || 0)
            + (e.desdoblea[field] || 0)
            + (e.errefortzuak[field] || 0))) * 100) / 100;
    }

    _r(n) {
        return Math.round((n || 0) * 100) / 100;
    }

    // GUZTIRA: horas (RPT) de eleanitza/desdoblea agrupadas por zikloa → taldea.
    // Devuelve [{zikloa, eleanitza, desdoblea, guztira, taldeak:[{taldea,...}]}].
    // Reparto por zikloa→taldea (tablas de gestión). Eleanitza = horas reales
    // de las copias HE_ (informativo); desdoblea/errefortzuak = reparto editable.
    guztiraByZikloTaldea() {
        return this.state.kopiaBanaketa || [];
    }

    // Totales generales (suma de todos los zikloak).
    guztiraTotal(field) {
        const rows = this.guztiraByZikloTaldea();
        return this._r(rows.reduce((s, z) => s + (z[field] || 0), 0));
    }

    // Recarga el resumen y las listas del mintegi tras crear/editar copias.
    async _refreshEleanitzaLaburpena() {
        if (!this.state.selectedMintegi) return;
        const [lab, mod, banaketa] = await Promise.all([
            this.orm.call("op.faculty", "get_perfilazio_eleanitza_laburpena",
                [this.state.selectedMintegi.id]),
            this.orm.call("op.faculty", "get_perfilazio_eleanitza_moduluak",
                [this.state.selectedMintegi.id]),
            this.orm.call("op.faculty", "get_perfilazio_kopia_banaketa",
                [this.state.selectedMintegi.id]),
        ]);
        this.state.eleanitzaModuluak = mod;
        this.state.kopiaBanaketa = banaketa;
        this._applyErrefLaburpena(lab);
    }

    // ¿El mintegi gestiona errefortzu en módulos? (TALDEAN o MIX)
    isErrefModuluak() {
        return this.state.errefortzuMota === 'taldean'
            || this.state.errefortzuMota === 'mix';
    }

    // Cambia el modo de errefortzu del mintegi (POLTSAN / TALDEAN / MIX).
    async onErrefortzuMotaChange(mota) {
        if (!this.state.selectedMintegi || this.state.errefortzuMota === mota) return;
        this.state.loading = true;
        const lab = await this.orm.call("op.faculty", "set_perfilazio_errefortzu_mota",
            [this.state.selectedMintegi.id, mota]);
        this._applyErrefLaburpena(lab);
        // Si ya no hay tramo de módulos y Errefortzuak está activo, salir.
        if (!this.isErrefModuluak() && this.state.mota === 'errefortzuak') {
            this.state.mota = '';
            await this._refreshKopiaPanel();
        }
        this.state.loading = false;
    }

    // MIX: fija las horas que van a POLTSAN (el resto van a módulos).
    async onErrefortzuPoltsanChange(ev) {
        if (!this.state.selectedMintegi) return;
        let v = parseFloat(ev.target.value);
        if (isNaN(v) || v < 0) v = 0;
        this.state.loading = true;
        const lab = await this.orm.call("op.faculty", "set_perfilazio_errefortzu_poltsan",
            [this.state.selectedMintegi.id, v]);
        this._applyErrefLaburpena(lab);
        ev.target.value = this.state.errefortzuPoltsan;
        this.state.loading = false;
    }

    _applyErrefLaburpena(lab) {
        this.state.eleanitzaLaburpena = lab;
        this.state.errefortzuMota = lab.errefortzu_mota || 'poltsan';
        this.state.errefortzuPoltsan = lab.errefortzu_poltsan || 0;
        this.state.errefortzuModulu = lab.errefortzu_modulu || 0;
    }

    // Edición del tope del mintegi (Tabla A, columna "ordu guztiak") para
    // desdoblea / errefortzuak. Eleanitza no es editable.
    async onKopiaLimitChange(mota, ev) {
        if (!this.state.selectedMintegi) return;
        let v = parseFloat(ev.target.value);
        if (isNaN(v) || v < 0) v = 0;
        this.state.loading = true;
        const lab = await this.orm.call("op.faculty", "set_perfilazio_kopia_limit",
            [this.state.selectedMintegi.id, mota, v]);
        this.state.eleanitzaLaburpena = lab;
        if (lab[mota]) ev.target.value = lab[mota].total;
        this.state.loading = false;
    }

    // Edición del reparto de un grupo (Tablas por zikloa) para desdoblea /
    // errefortzuak. Acotado al tope libre del mintegi.
    async onKopiaGroupChange(batchId, mota, ev) {
        let v = parseFloat(ev.target.value);
        if (isNaN(v) || v < 0) v = 0;
        this.state.loading = true;
        const res = await this.orm.call("op.faculty", "set_perfilazio_kopia_group_orduak",
            [batchId, mota, v]);
        // Recarga el resumen (esleitzeke) y el reparto (tablas por zikloa).
        await this._refreshEleanitzaLaburpena();
        if (res && res.orduak !== undefined) ev.target.value = res.orduak;
        // Si el grupo editado es la taldea activa, refresca la cabecera (Erabilita).
        if (this.usesOrduak() && this.state.selectedBatch
                && this.state.selectedBatch.id === batchId) {
            await this._refreshDesdoInfo();
        }
        this.state.loading = false;
    }

    async onZikloaChange(ev) {
        const id = parseInt(ev.target.value) || null;
        this.state.selectedZikloa = this.state.zikloak.find(z => z.id === id) || null;
        this.state.selectedBatch = null;
        this.state.batches = [];
        this._resetKopiak();
        if (!id) return;
        this.state.loading = true;
        this.state.batches = await this.orm.call("op.faculty", "get_perfilazio_batches", [id]);
        this.state.loading = false;
    }

    async onBatchChange(ev) {
        const id = parseInt(ev.target.value) || null;
        this.state.selectedBatch = this.state.batches.find(b => b.id === id) || null;
        this.state.zikloModuluak = [];
        this.state.selectedKopiak = {};
        // Las copias son por taldea: al cambiar de taldea recargar el panel.
        if (this.isKopiakActive()) await this._refreshKopiaPanel();
    }

    // ── Eleanitza / Desdoblea / Errefortzuak (modo único) ────────────
    _resetKopiak() {
        this.state.mota = '';
        this.state.zikloModuluak = [];
        this.state.selectedKopiak = {};
        this.state.desdoOrduak = {};
        this.state.desdoInfo = { total: 0, used: 0, remaining: 0 };
    }

    isKopiakActive() {
        return !!this.state.mota;
    }

    // Modos que llevan horas por módulo (columna editable): desdoble y errefortzu.
    usesOrduak() {
        return this.state.mota === 'desdoblea' || this.state.mota === 'errefortzuak';
    }

    selectedKopiaCount() {
        return Object.values(this.state.selectedKopiak).filter(Boolean).length;
    }

    _activeKopiaPrefix() {
        return { eleanitza: 'HE_', desdoblea: 'DESDO_', errefortzuak: 'ERREF_' }[this.state.mota] || '';
    }

    _activeKopiaFlag() {
        return { eleanitza: 'has_he', desdoblea: 'has_desdo', errefortzuak: 'has_erref' }[this.state.mota];
    }

    // ¿La copia del modo activo ya existe para este módulo origen?
    _kopiaExists(modulu) {
        const flag = this._activeKopiaFlag();
        return flag ? !!modulu[flag] : false;
    }

    // Horas por defecto del modo con horas (desdoble/errefortzu) para un módulo.
    _defaultOrduak(modulu) {
        if (this.state.mota === 'errefortzuak') {
            return modulu.erref_orduak !== undefined ? modulu.erref_orduak : modulu.rpt_total;
        }
        return modulu.desdo_orduak !== undefined ? modulu.desdo_orduak : modulu.rpt_total;
    }

    // Cambio en el desplegable de modo (mutuamente excluyente).
    async onMotaChange(ev) {
        this.state.mota = ev.target.value || '';
        await this._refreshKopiaPanel();
    }

    async _ensureZikloModuluak() {
        // Solo los módulos de la taldea seleccionada (códigos <taldea>_XXX)
        if (!this.state.selectedBatch) { this.state.zikloModuluak = []; return; }
        this.state.loading = true;
        this.state.zikloModuluak = await this.orm.call(
            "op.faculty", "get_perfilazio_ziklo_moduluak", [this.state.selectedBatch.id]);
        this.state.loading = false;
    }

    // La selección refleja qué módulos YA tienen su copia (HE_/DESDO_) creada
    _initKopiaSelection() {
        const flag = this._activeKopiaFlag();
        const sel = {};
        const desdo = {};
        for (const m of this.state.zikloModuluak) {
            sel[m.id] = !!m[flag];
            desdo[m.id] = this._defaultOrduak(m);
        }
        this.state.selectedKopiak = sel;
        this.state.desdoOrduak = desdo;
    }

    async _refreshKopiaPanel() {
        if (!this.isKopiakActive()) {
            this.state.zikloModuluak = [];
            this.state.selectedKopiak = {};
            return;
        }
        if (!this.state.zikloModuluak.length) await this._ensureZikloModuluak();
        this._initKopiaSelection();
        await this._refreshDesdoInfo();
    }

    async _refreshDesdoInfo() {
        if (!this.usesOrduak() || !this.state.selectedBatch) {
            this.state.desdoInfo = { total: 0, used: 0, remaining: 0 };
            return;
        }
        this.state.desdoInfo = await this.orm.call(
            "op.faculty", "get_perfilazio_desdoble_info",
            [this.state.selectedBatch.id, this.state.mota]);
    }


    // Clic = crear la copia (si no existe) o eliminarla (si existe).
    async toggleKopia(modulu) {
        const prefix = this._activeKopiaPrefix();
        if (!prefix) return;
        this.state.loading = true;
        const args = [modulu.id, prefix];
        // Con Desdoblea/Errefortzuak, la copia DESDO_/ERREF_ se crea con las
        // horas fijadas en la columna de orduak (en vez del RPT completo).
        if (this.usesOrduak()) {
            args.push(this.state.desdoOrduak[modulu.id]);
        }
        const res = await this.orm.call("op.faculty", "toggle_perfilazio_kopia", args);
        const flag = this._activeKopiaFlag();
        const zm = this.state.zikloModuluak.find(x => x.id === modulu.id);
        if (zm) zm[flag] = res.exists;
        this.state.selectedKopiak[modulu.id] = res.exists;
        if (res.exists && res.orduak !== null && res.orduak !== undefined) {
            this.state.desdoOrduak[modulu.id] = res.orduak;
        } else if (!res.exists) {
            this.state.desdoOrduak[modulu.id] = modulu.rpt_total || 0;
        }
        await this._refreshDesdoInfo();
        await this._refreshEleanitzaLaburpena();
        this.state.loading = false;
    }

    // Cambio en "Desdoble Orduak": acota a [0, RPT] (y al tope libre del grupo
    // si la copia aún no existe). Si la copia DESDO_ ya existe, actualiza horas.
    async onDesdoOrduakChange(modulu, ev) {
        const exists = this._kopiaExists(modulu);
        let v = parseFloat(ev.target.value);
        let max = modulu.rpt_total || 0;
        // El tope del grupo (reparto) acota desdoble y errefortzu por igual.
        if (!exists && this.usesOrduak() && this.state.desdoInfo.total > 0) {
            max = Math.min(max, this.state.desdoInfo.remaining);
        }
        if (isNaN(v) || v < 0) v = 0;
        if (v > max) v = max;
        v = Math.round(v * 100) / 100;
        this.state.desdoOrduak[modulu.id] = v;
        ev.target.value = v;
        if (!exists) return;  // aún no creada: se usará al crearla
        this.state.loading = true;
        const res = await this.orm.call(
            "op.faculty", "set_perfilazio_desdoble_orduak",
            [modulu.id, v, this._activeKopiaPrefix()]);
        if (res && res.orduak !== undefined) {
            this.state.desdoOrduak[modulu.id] = res.orduak;
        }
        await this._refreshDesdoInfo();
        await this._refreshEleanitzaLaburpena();
        this.state.loading = false;
    }

    // Color de la fila seleccionada: verde (HE) · morado (DESDO) · naranja (ERREF)
    kopiaRowClass(modulu) {
        if (!this.state.selectedKopiak[modulu.id]) return '';
        return { eleanitza: 'pfz-kopia--he', desdoblea: 'pfz-kopia--desdo',
                 errefortzuak: 'pfz-kopia--erref' }[this.state.mota] || '';
    }
}

registry.category("actions").add("desdoble_he_action", DesdobleHe);
