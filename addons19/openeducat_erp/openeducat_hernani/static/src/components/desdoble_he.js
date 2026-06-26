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
            },
            // Listas de módulos copia del mintegi (HE_ y DESDO_)
            eleanitzaModuluak: { eleanitza: [], desdoblea: [] },

            // Desdoble / Eleanitza (mutuamente excluyentes)
            eleanitza: 'EZ',
            desdoblea: 'EZ',
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
        const [zikloak, eleanitza, eleanitzaMod] = await Promise.all([
            this.orm.call("op.faculty", "get_perfilazio_zikloak", [id]),
            this.orm.call("op.faculty", "get_perfilazio_eleanitza_laburpena", [id]),
            this.orm.call("op.faculty", "get_perfilazio_eleanitza_moduluak", [id]),
        ]);
        this.state.zikloak = zikloak;
        this.state.eleanitzaLaburpena = eleanitza;
        this.state.eleanitzaModuluak = eleanitzaMod;
        this.state.loading = false;
    }

    _resetEleanitzaLaburpena() {
        this.state.eleanitzaLaburpena = {
            eleanitza: { total: 0, pending: 0 },
            desdoblea: { total: 0, pending: 0 },
        };
        this.state.eleanitzaModuluak = { eleanitza: [], desdoblea: [] };
    }

    // GUZTIRA de la tabla Eleanitza / Desdobleak (suma eleanitza + desdoblea).
    eleanitzaGuztira(field) {
        const e = this.state.eleanitzaLaburpena;
        return Math.round(((e.eleanitza[field] || 0) + (e.desdoblea[field] || 0)) * 100) / 100;
    }

    _r(n) {
        return Math.round((n || 0) * 100) / 100;
    }

    // GUZTIRA: horas (RPT) de eleanitza/desdoblea agrupadas por zikloa → taldea.
    // Devuelve [{zikloa, eleanitza, desdoblea, guztira, taldeak:[{taldea,...}]}].
    guztiraByZikloTaldea() {
        const acc = {};  // zikloa → taldea → {eleanitza, desdoblea}
        const add = (list, field) => {
            for (const m of (list || [])) {
                const z = m.zikloa || '—', t = m.taldea || '—';
                (acc[z] = acc[z] || {});
                (acc[z][t] = acc[z][t] || { eleanitza: 0, desdoblea: 0 });
                acc[z][t][field] += m.rpt || 0;
            }
        };
        add(this.state.eleanitzaModuluak.eleanitza, 'eleanitza');
        add(this.state.eleanitzaModuluak.desdoblea, 'desdoblea');
        return Object.keys(acc).sort().map(z => {
            const taldeak = Object.keys(acc[z]).sort().map(t => {
                const e = this._r(acc[z][t].eleanitza);
                const d = this._r(acc[z][t].desdoblea);
                return { taldea: t, eleanitza: e, desdoblea: d, guztira: this._r(e + d) };
            });
            const ze = this._r(taldeak.reduce((s, x) => s + x.eleanitza, 0));
            const zd = this._r(taldeak.reduce((s, x) => s + x.desdoblea, 0));
            return { zikloa: z, taldeak, eleanitza: ze, desdoblea: zd, guztira: this._r(ze + zd) };
        });
    }

    // Totales generales (suma de todos los zikloak).
    guztiraTotal(field) {
        const rows = this.guztiraByZikloTaldea();
        return this._r(rows.reduce((s, z) => s + (z[field] || 0), 0));
    }

    // Recarga el resumen y las listas del mintegi tras crear/editar copias.
    async _refreshEleanitzaLaburpena() {
        if (!this.state.selectedMintegi) return;
        const [lab, mod] = await Promise.all([
            this.orm.call("op.faculty", "get_perfilazio_eleanitza_laburpena",
                [this.state.selectedMintegi.id]),
            this.orm.call("op.faculty", "get_perfilazio_eleanitza_moduluak",
                [this.state.selectedMintegi.id]),
        ]);
        this.state.eleanitzaLaburpena = lab;
        this.state.eleanitzaModuluak = mod;
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

    // ── Desdoble / Eleanitza ─────────────────────────────────────────
    _resetKopiak() {
        this.state.eleanitza = 'EZ';
        this.state.desdoblea = 'EZ';
        this.state.zikloModuluak = [];
        this.state.selectedKopiak = {};
        this.state.desdoOrduak = {};
        this.state.desdoInfo = { total: 0, used: 0, remaining: 0 };
    }

    isKopiakActive() {
        return this.state.eleanitza === 'BAI' || this.state.desdoblea === 'BAI';
    }

    selectedKopiaCount() {
        return Object.values(this.state.selectedKopiak).filter(Boolean).length;
    }

    _activeKopiaPrefix() {
        return this.state.eleanitza === 'BAI' ? 'HE_'
            : (this.state.desdoblea === 'BAI' ? 'DESDO_' : '');
    }

    _activeKopiaFlag() {
        return this.state.eleanitza === 'BAI' ? 'has_he' : 'has_desdo';
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
            desdo[m.id] = m.desdo_orduak !== undefined ? m.desdo_orduak : m.rpt_total;
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
        if (this.state.desdoblea !== 'BAI' || !this.state.selectedBatch) {
            this.state.desdoInfo = { total: 0, used: 0, remaining: 0 };
            return;
        }
        this.state.desdoInfo = await this.orm.call(
            "op.faculty", "get_perfilazio_desdoble_info", [this.state.selectedBatch.id]);
    }

    async onDesdoTotalChange(ev) {
        if (!this.state.selectedBatch) return;
        let v = parseFloat(ev.target.value);
        if (isNaN(v) || v < 0) v = 0;
        this.state.loading = true;
        this.state.desdoInfo = await this.orm.call(
            "op.faculty", "set_perfilazio_desdoble_total",
            [this.state.selectedBatch.id, v]);
        ev.target.value = this.state.desdoInfo.total;
        this.state.loading = false;
    }

    async toggleEleanitza() {
        this.state.eleanitza = this.state.eleanitza === 'BAI' ? 'EZ' : 'BAI';
        if (this.state.eleanitza === 'BAI') this.state.desdoblea = 'EZ';  // excluyentes
        await this._refreshKopiaPanel();
    }

    async toggleDesdoblea() {
        this.state.desdoblea = this.state.desdoblea === 'BAI' ? 'EZ' : 'BAI';
        if (this.state.desdoblea === 'BAI') this.state.eleanitza = 'EZ';  // excluyentes
        await this._refreshKopiaPanel();
    }

    // Clic = crear la copia (si no existe) o eliminarla (si existe).
    async toggleKopia(modulu) {
        const prefix = this._activeKopiaPrefix();
        if (!prefix) return;
        this.state.loading = true;
        const args = [modulu.id, prefix];
        // Con Desdoblea, la copia DESDO_ se crea con las horas fijadas en la
        // columna "Desdoble Orduak" (en vez del RPT completo del módulo).
        if (this.state.desdoblea === 'BAI') {
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
        let v = parseFloat(ev.target.value);
        let max = modulu.rpt_total || 0;
        if (!modulu.has_desdo && this.state.desdoInfo.total > 0) {
            max = Math.min(max, this.state.desdoInfo.remaining);
        }
        if (isNaN(v) || v < 0) v = 0;
        if (v > max) v = max;
        v = Math.round(v * 100) / 100;
        this.state.desdoOrduak[modulu.id] = v;
        ev.target.value = v;
        if (!modulu.has_desdo) return;  // aún no creada: se usará al crearla
        this.state.loading = true;
        const res = await this.orm.call(
            "op.faculty", "set_perfilazio_desdoble_orduak", [modulu.id, v]);
        if (res && res.orduak !== undefined) {
            this.state.desdoOrduak[modulu.id] = res.orduak;
        }
        await this._refreshDesdoInfo();
        await this._refreshEleanitzaLaburpena();
        this.state.loading = false;
    }

    // Color de la fila seleccionada: verde (HE/eleanitza) o morado (DESDO)
    kopiaRowClass(modulu) {
        if (!this.state.selectedKopiak[modulu.id]) return '';
        return this.state.desdoblea === 'BAI' ? 'pfz-kopia--desdo' : 'pfz-kopia--he';
    }
}

registry.category("actions").add("desdoble_he_action", DesdobleHe);
