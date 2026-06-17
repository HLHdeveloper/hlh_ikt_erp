/** @odoo-module */
import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

class Perfilazioak extends Component {
    static template = "openeducat_hernani.Perfilazioak";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        // Departamentos a los que se puede asignar un módulo TUTO (3 desplegables)
        this.TUTO_DEPTS = ['ORIENTA', 'LPO', 'INGELES'];
        this.TUTO_LABELS = { ORIENTA: 'ORI', LPO: 'LPO', INGELES: 'ING' };
        this.state = useState({
            mintegiak: [],
            zikloak: [],
            batches: [],
            selectedMintegi: null,
            selectedZikloa: null,
            selectedBatch: null,

            irakasleak: [],
            moduluak: [],
            // Candidatos por departamento para módulos especiales (no técnicos)
            specialIrakasleak: {},
            // Candidatos (ORIENTA/LPO/INGELES) para módulos TUTO
            tutoIrakasleak: {},

            // Desdoble / Eleanitza: duplicar módulos del ciclo con prefijo
            eleanitza: 'EZ',
            desdoblea: 'EZ',
            zikloModuluak: [],
            selectedKopiak: {},
            // Horas de desdoble por módulo (clave = id del módulo origen).
            // Solo se usan con Desdoblea: la copia DESDO_ se crea con estas
            // horas en vez del RPT completo.
            desdoOrduak: {},
            // Tope total de horas de desdoble del grupo (taldea) y consumo.
            desdoInfo: { total: 0, used: 0, remaining: 0 },
            kopiakMsg: '',

            // Apoyo Educativo (solo ciclos OLH*): grupos I/II/III con tope RPT
            apoyoKodea: '',
            apoyoData: { id: null, guztira_orduak: 0, sum_rpt: 0, modules: [] },
            apoyoNew: { code: '', pt_pes: '', orduak: 0, kurtsoa: '',
                        banaketa_id: '', gela_orduak: 0, rpt_total: 0, orduak_zorretan: 0 },
            banaketaAukerak: [],

            selectedFaculty: null,
            karguak: [],

            addingKargu: false,
            allKarguak: [],
            newKarguId: null,
            newKarguOrduak: 0,
            newKarguRemaining: 0,
            newKarguAllowZero: false,
            newKarguAllowDecimal: false,

            resumenModuluak: [],

            ingelesaMode: false,

            showLaburpena: false,
            laburpenaData: [],
            laburpenaOrdezkoak: [],

            showBertsioak: false,
            bertsioak: [],

            taldeakLaburpena: [],
            mintegiKarguak: [],

            loading: false,
        });
        onWillStart(() => this._loadMintegiak());
    }

    async _loadMintegiak() {
        this.state.mintegiak = await this.orm.call("op.faculty", "get_perfilazio_mintegiak", []);
    }

    async onMintegiChange(ev) {
        const id = parseInt(ev.target.value) || null;
        this.state.selectedMintegi = this.state.mintegiak.find(m => m.id === id) || null;
        this.state.selectedZikloa = null;
        this.state.selectedBatch = null;
        this.state.zikloak = [];
        this.state.batches = [];
        this.state.moduluak = [];
        this.state.specialIrakasleak = {};
        this.state.irakasleak = [];
        this.state.selectedFaculty = null;
        this.state.karguak = [];
        this.state.addingKargu = false;
        this.state.ingelesaMode = false;
        this.state.showLaburpena = false;
        this.state.laburpenaData = [];
        this._resetKopiak();
        this._resetApoyo();

        if (!id) return;
        this.state.loading = true;
        const isIngelesa = (this.state.selectedMintegi.code || '').toUpperCase() === 'INGELES';
        if (isIngelesa) {
            // Ingelesa: sin zikloa/taldea, se muestran todos los módulos _ING
            const [irakasleak, moduluak] = await Promise.all([
                this.orm.call("op.faculty", "get_perfilazio_irakasleak", [id]),
                this.orm.call("op.faculty", "get_perfilazio_ingelesa_moduluak", []),
            ]);
            this.state.irakasleak = irakasleak;
            this.state.moduluak = moduluak;
            this.state.ingelesaMode = true;
            await this._loadSpecialIrakasleak();
        } else {
            const [zikloak, irakasleak] = await Promise.all([
                this.orm.call("op.faculty", "get_perfilazio_zikloak", [id]),
                this.orm.call("op.faculty", "get_perfilazio_irakasleak", [id]),
            ]);
            this.state.zikloak = zikloak;
            this.state.irakasleak = irakasleak;
        }
        await this._refreshTaldeakLaburpena();
        this.state.loading = false;
    }

    async _reloadModuluak() {
        if (this.state.ingelesaMode) {
            this.state.moduluak = await this.orm.call("op.faculty", "get_perfilazio_ingelesa_moduluak", []);
        } else if (this.state.selectedBatch) {
            this.state.moduluak = await this.orm.call("op.faculty", "get_perfilazio_moduluak", [this.state.selectedBatch.id]);
        }
        await this._loadSpecialIrakasleak();
    }

    // Carga los profesores candidatos de los departamentos referenciados por
    // los módulos especiales presentes en la lista actual de moduluak.
    async _loadSpecialIrakasleak() {
        const codes = [...new Set(this.state.moduluak.map(m => m.special_dept).filter(Boolean))];
        if (!codes.length) {
            this.state.specialIrakasleak = {};
            return;
        }
        this.state.specialIrakasleak = await this.orm.call(
            "op.faculty", "get_special_modulu_irakasleak", [codes]);
        await this._loadTutoIrakasleak();
    }

    // Profesores candidatos para un módulo especial (según su departamento)
    specialOptions(modulu) {
        return (modulu.special_dept && this.state.specialIrakasleak[modulu.special_dept]) || [];
    }

    // Carga (una vez) los profesores de ORIENTA/LPO/INGELES para módulos TUTO
    async _loadTutoIrakasleak() {
        const hasTuto = this.state.moduluak.some(m => m.tuto);
        if (!hasTuto || Object.keys(this.state.tutoIrakasleak).length) return;
        this.state.tutoIrakasleak = await this.orm.call(
            "op.faculty", "get_special_modulu_irakasleak", [this.TUTO_DEPTS]);
    }

    tutoOptions(deptCode) {
        return this.state.tutoIrakasleak[deptCode] || [];
    }

    tutoLabel(deptCode) {
        return this.TUTO_LABELS[deptCode] || deptCode;
    }

    async onZikloaChange(ev) {
        const id = parseInt(ev.target.value) || null;
        this.state.selectedZikloa = this.state.zikloak.find(z => z.id === id) || null;
        this.state.selectedBatch = null;
        this.state.batches = [];
        this.state.moduluak = [];
        this._resetKopiak();
        this._resetApoyo();

        if (!id) return;
        this.state.loading = true;
        this.state.batches = await this.orm.call("op.faculty", "get_perfilazio_batches", [id]);
        this.state.loading = false;
    }

    // ── Desdoble / Eleanitza ─────────────────────────────────────────
    _resetKopiak() {
        this.state.eleanitza = 'EZ';
        this.state.desdoblea = 'EZ';
        this.state.zikloModuluak = [];
        this.state.selectedKopiak = {};
        this.state.kopiakMsg = '';
    }

    isKopiakActive() {
        return this.state.eleanitza === 'BAI' || this.state.desdoblea === 'BAI';
    }

    selectedKopiaCount() {
        return Object.values(this.state.selectedKopiak).filter(Boolean).length;
    }

    // Operación activa (mutuamente excluyentes): prefijo y flag de existencia
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
            // Horas de desdoble: las de la copia existente, o el RPT completo
            // como valor por defecto (lo aporta el servidor en desdo_orduak).
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

    // Tope total de horas de desdoble del grupo y horas consumidas.
    async _refreshDesdoInfo() {
        if (this.state.desdoblea !== 'BAI' || !this.state.selectedBatch) {
            this.state.desdoInfo = { total: 0, used: 0, remaining: 0 };
            return;
        }
        this.state.desdoInfo = await this.orm.call(
            "op.faculty", "get_perfilazio_desdoble_info",
            [this.state.selectedBatch.id]);
    }

    // Cambio del tope total de horas de desdoble del grupo.
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
        // Con Desdoblea, la copia DESDO_ se crea con las horas fijadas en la
        // columna "Desdoble Orduak" (en vez del RPT completo del módulo).
        const args = [modulu.id, prefix];
        if (this.state.desdoblea === 'BAI') {
            args.push(this.state.desdoOrduak[modulu.id]);
        }
        const res = await this.orm.call(
            "op.faculty", "toggle_perfilazio_kopia", args);
        const flag = this._activeKopiaFlag();
        const zm = this.state.zikloModuluak.find(x => x.id === modulu.id);
        if (zm) zm[flag] = res.exists;
        this.state.selectedKopiak[modulu.id] = res.exists;
        // La copia puede haberse creado con menos horas de las pedidas si el
        // tope del grupo no daba para más: reflejar las realmente aplicadas.
        if (res.exists && res.orduak !== null && res.orduak !== undefined) {
            this.state.desdoOrduak[modulu.id] = res.orduak;
        }
        this._recomputeZikloIndicator();
        // Al crear/eliminar una copia puede cambiar la perfilación de algún
        // profesor (si la copia estaba asignada): recargar moduluak, irakasleak
        // y resumen para recalcular horas.
        if (this.state.selectedBatch) await this._reloadModuluak();
        await this._refreshIrakasleak();
        await this._refreshResumen();
        await this._refreshDesdoInfo();
        this.state.loading = false;
    }

    // Cambio en la columna "Desdoble Orduak": acota a [0, RPT] y, si la copia
    // DESDO_ ya existe, actualiza sus horas en caliente (recalcula perfilación).
    async onDesdoOrduakChange(modulu, ev) {
        let v = parseFloat(ev.target.value);
        let max = modulu.rpt_total || 0;
        // Tope del grupo: para una copia aún no creada, lo libre es remaining.
        if (!modulu.has_desdo && this.state.desdoInfo.total > 0) {
            max = Math.min(max, this.state.desdoInfo.remaining);
        }
        if (isNaN(v) || v < 0) v = 0;
        if (v > max) v = max;
        v = Math.round(v * 100) / 100;
        this.state.desdoOrduak[modulu.id] = v;
        ev.target.value = v;  // reflejar el valor acotado en el input
        if (!modulu.has_desdo) return;  // aún no creada: se usará al crearla
        this.state.loading = true;
        const res = await this.orm.call(
            "op.faculty", "set_perfilazio_desdoble_orduak", [modulu.id, v]);
        // El servidor acota también al tope del grupo: reflejar lo aplicado.
        if (res && res.orduak !== undefined) {
            this.state.desdoOrduak[modulu.id] = res.orduak;
        }
        if (this.state.selectedBatch) await this._reloadModuluak();
        await this._refreshIrakasleak();
        await this._refreshResumen();
        await this._refreshDesdoInfo();
        this.state.loading = false;
    }

    // Color de la fila seleccionada: verde (HE/eleanitza) o morado (DESDO/desdoble)
    kopiaRowClass(modulu) {
        if (!this.state.selectedKopiak[modulu.id]) return '';
        return this.state.desdoblea === 'BAI' ? 'pfz-kopia--desdo' : 'pfz-kopia--he';
    }

    _recomputeZikloIndicator() {
        if (!this.state.selectedZikloa) return;
        const he = this.state.zikloModuluak.some(m => m.has_he);
        const desdo = this.state.zikloModuluak.some(m => m.has_desdo);
        this.state.selectedZikloa.has_he = he;
        this.state.selectedZikloa.has_desdo = desdo;
        const z = this.state.zikloak.find(x => x.id === this.state.selectedZikloa.id);
        if (z) { z.has_he = he; z.has_desdo = desdo; }
    }

    async _refreshIrakasleak() {
        if (!this.state.selectedMintegi || this.state.ingelesaMode) return;
        const fresh = await this.orm.call(
            "op.faculty", "get_perfilazio_irakasleak", [this.state.selectedMintegi.id]);
        this.state.irakasleak = fresh;
        if (this.state.selectedFaculty) {
            const f = fresh.find(x => x.id === this.state.selectedFaculty.id);
            if (f) {
                this.state.selectedFaculty.orduak = f.orduak;
                this.state.selectedFaculty.overload = f.overload;
                this.state.selectedFaculty.gela = f.gela;
            }
        }
    }

    // Mintegiko taldeak: módulos sin asignar / total (consulta servidor)
    async _refreshTaldeakLaburpena() {
        if (!this.state.selectedMintegi || this.state.ingelesaMode) {
            this.state.taldeakLaburpena = [];
            this.state.mintegiKarguak = [];
            return;
        }
        this.state.taldeakLaburpena = await this.orm.call(
            "op.faculty", "get_perfilazio_taldeak_laburpena",
            [this.state.selectedMintegi.id]);
        this.state.mintegiKarguak = await this.orm.call(
            "op.faculty", "get_perfilazio_mintegi_karguak",
            [this.state.selectedMintegi.id]);
    }

    // GUZTIRA de "Mintegiko karguak": suma de la columna "ordu guztiak".
    mintegiKarguakGuztira() {
        const t = this.state.mintegiKarguak.reduce((s, mk) => s + (mk.total || 0), 0);
        return Math.round(t * 100) / 100;
    }

    // Plazen laburpena: por distintivo PT/PES de los profesores, suma sus
    // horas y las convierte a plazas (17h = 1; 6h=1/3, 9h=1/2, 12h=2/3).
    plazakLaburpena() {
        const hours = { PES: 0, PT: 0 };
        for (const f of this.state.irakasleak) {
            const cat = f.pt_pes === 'PT' ? 'PT' : 'PES';
            hours[cat] += f.orduak || 0;
        }
        return ['PES', 'PT'].map(cat => ({ cat, label: this._plazaLabel(hours[cat]) }));
    }

    _plazaLabel(h) {
        h = Math.round(h * 100) / 100;
        const whole = Math.floor(h / 17 + 1e-9);
        const rem = Math.round((h - whole * 17) * 100) / 100;
        const parts = [];
        if (whole) parts.push(String(whole));
        if (rem > 0.001) {
            const FR = [[6, '1/3'], [9, '1/2'], [12, '2/3']];
            const m = FR.find(([hh]) => Math.abs(rem - hh) < 0.1);
            parts.push(m ? m[1] : (Number.isInteger(rem) ? rem + 'h' : rem.toFixed(1) + 'h'));
        }
        return parts.length ? parts.join(' + ') : '0';
    }

    // ── Apoyo Educativo ──────────────────────────────────────────────
    _emptyApoyoNew(kurtsoa = '') {
        return { code: '', pt_pes: '', orduak: 0, kurtsoa,
                 banaketa_id: '', gela_orduak: 0, rpt_total: 0, orduak_zorretan: 0 };
    }

    // Kurtsoa según el curso del taldea: 1OLH… → 1, 2OLH… → 2, resto → 3
    _kurtsoaFromBatch() {
        const name = (this.state.selectedBatch && this.state.selectedBatch.name) || '';
        const d = name.trim().charAt(0);
        return (d === '1' || d === '2') ? d : '3';
    }

    _resetApoyo() {
        this.state.apoyoKodea = '';
        this.state.apoyoData = { id: null, guztira_orduak: 0, sum_rpt: 0, modules: [] };
        this.state.apoyoNew = this._emptyApoyoNew();
    }

    // El ciclo permite Apoyo Educativo si es OLHELE / OLHMEK (OLH*)
    isApoyoZikloa() {
        const n = this.state.selectedZikloa && this.state.selectedZikloa.name;
        return !!n && n.toUpperCase().startsWith('OLH');
    }

    apoyoLabel() {
        return this.state.apoyoKodea ? 'APOYO_EDUCATIVO_' + this.state.apoyoKodea : '';
    }

    // El código del multzo (I/II/III) se deduce del curso del taldea
    // seleccionado (1OLHELE3 → I, 2OLHELE3 → II, 3OLHELE3 → III).
    _apoyoKodeaFromBatch() {
        const name = (this.state.selectedBatch && this.state.selectedBatch.name) || '';
        return { '1': 'I', '2': 'II', '3': 'III' }[name.trim().charAt(0)] || 'I';
    }

    async openApoyo() {
        if (!this.state.selectedBatch) return;
        const kodea = this._apoyoKodeaFromBatch();
        this.state.apoyoKodea = kodea;
        this.state.apoyoNew = this._emptyApoyoNew(this._kurtsoaFromBatch());
        this.state.loading = true;
        if (!this.state.banaketaAukerak.length) {
            this.state.banaketaAukerak = await this.orm.call(
                "op.faculty", "get_banaketa_aukerak", []);
        }
        this.state.apoyoData = await this.orm.call(
            "op.faculty", "get_apoyo_taldea",
            [this.state.selectedBatch.id, kodea]);
        this.state.loading = false;
    }

    closeApoyo() {
        this._resetApoyo();
    }

    banaketaSel(id) {
        return String(this.state.apoyoNew.banaketa_id) === String(id);
    }

    // El multzo está lleno si la suma de RPT iguala o supera las horas totales
    apoyoFull() {
        const d = this.state.apoyoData;
        return d.guztira_orduak > 0 && d.sum_rpt >= d.guztira_orduak;
    }

    async onApoyoGuztiraChange(ev) {
        const orduak = parseFloat(ev.target.value) || 0;
        this.state.apoyoData = await this.orm.call(
            "op.faculty", "set_apoyo_guztira",
            [this.state.selectedBatch.id, this.state.apoyoKodea, orduak]);
    }

    onApoyoNewInput(field, ev) {
        const numeric = ['orduak', 'gela_orduak', 'rpt_total', 'orduak_zorretan'];
        const v = ev.target.value;
        this.state.apoyoNew[field] = numeric.includes(field) ? (parseFloat(v) || 0) : v;
    }

    async createApoyoModulu() {
        if (this.apoyoFull()) {
            this.notification.add("Multzoa beteta dago. Ezin da modulu gehiago gehitu.",
                { type: 'warning' });
            return;
        }
        if (!this.state.apoyoNew.code.trim()) {
            this.notification.add("Kodea beharrezkoa da.", { type: 'warning' });
            return;
        }
        this.state.loading = true;
        try {
            this.state.apoyoData = await this.orm.call(
                "op.faculty", "create_apoyo_modulu",
                [this.state.selectedBatch.id, this.state.apoyoKodea, this.state.apoyoNew]);
            this.state.apoyoNew = this._emptyApoyoNew(this._kurtsoaFromBatch());
            // Reflejar el nuevo módulo en el listado general de la taldea
            await this._reloadModuluak();
            this.notification.add("Modulua sortu da.", { type: 'success' });
        } finally {
            this.state.loading = false;
        }
    }

    async deleteApoyoModulu(modulu) {
        if (!confirm(`"${modulu.code}" ezabatu nahi duzu?`)) return;
        this.state.loading = true;
        this.state.apoyoData = await this.orm.call(
            "op.faculty", "delete_apoyo_modulu", [modulu.id]);
        await this._reloadModuluak();
        this.state.loading = false;
    }

    async onBatchChange(ev) {
        const id = parseInt(ev.target.value) || null;
        this.state.selectedBatch = this.state.batches.find(b => b.id === id) || null;
        this.state.moduluak = [];
        this.state.zikloModuluak = [];  // kopiatu panela taldez aldatzean birkargatu
        this._resetApoyo();

        if (!id) return;
        this.state.loading = true;
        this.state.moduluak = await this.orm.call("op.faculty", "get_perfilazio_moduluak", [id]);
        await this._loadSpecialIrakasleak();
        if (this.isKopiakActive()) await this._refreshKopiaPanel();
        this.state.loading = false;
    }

    async onFacultyClick(faculty) {
        if (this.state.selectedFaculty && this.state.selectedFaculty.id === faculty.id) {
            this.state.selectedFaculty = null;
            this.state.karguak = [];
            this.state.resumenModuluak = [];
            this.state.addingKargu = false;
            return;
        }
        this.state.selectedFaculty = faculty;
        this.state.addingKargu = false;
        this.state.karguak = await this.orm.call("op.faculty", "get_perfilazio_karguak", [faculty.id]);
        await this._refreshResumen();
    }

    // Alterna manualmente el distintivo PT/PES del profesor (persistente).
    async togglePtPes(f) {
        const val = await this.orm.call("op.faculty", "toggle_perfilazio_pt_pes", [f.id]);
        f.pt_pes = val;
        if (this.state.selectedFaculty && this.state.selectedFaculty.id === f.id) {
            this.state.selectedFaculty.pt_pes = val;
        }
    }

    async onModuluClick(modulu) {
        // Los módulos especiales (no técnicos) solo se asignan mediante el
        // desplegable de la columna Irakaslea, no con los profesores del mintegi.
        if (modulu.special_dept) return;
        if (!this.state.selectedFaculty) return;
        const facultyId = this.state.selectedFaculty.id;
        // Toggle: if assigned to selected faculty → unassign; else → assign
        const newFacultyId = modulu.faculty_id === facultyId ? null : facultyId;

        this.state.loading = true;
        const affected = await this.orm.call("op.faculty", "assign_perfilazio_modulu", [modulu.id, newFacultyId]);

        const idx = this.state.moduluak.findIndex(m => m.id === modulu.id);
        if (idx >= 0) {
            this.state.moduluak[idx].faculty_id = newFacultyId;
            this.state.moduluak[idx].faculty_name = newFacultyId ? this.state.selectedFaculty.name : null;
        }

        for (const upd of affected) {
            const fidx = this.state.irakasleak.findIndex(f => f.id === upd.id);
            if (fidx >= 0) {
                this.state.irakasleak[fidx].orduak = upd.orduak;
                this.state.irakasleak[fidx].overload = upd.overload;
                this.state.irakasleak[fidx].gela = upd.gela;
                if (upd.pt_pes !== undefined) this.state.irakasleak[fidx].pt_pes = upd.pt_pes;
            }
            if (this.state.selectedFaculty && this.state.selectedFaculty.id === upd.id) {
                this.state.selectedFaculty.orduak = upd.orduak;
                this.state.selectedFaculty.overload = upd.overload;
                this.state.selectedFaculty.gela = upd.gela;
                if (upd.pt_pes !== undefined) this.state.selectedFaculty.pt_pes = upd.pt_pes;
            }
        }
        await this._refreshResumen();
        await this._refreshTaldeakLaburpena();
        this.state.loading = false;
    }

    // Asignación de un módulo especial a un profesor del departamento que lo
    // imparte (Ingelesa / Orientazioa / LPO), elegido en el desplegable.
    // Asigna un módulo a un profesor (o lo desasigna) y refresca horas/resumen.
    // facultyName: nombre a mostrar en la columna Irakaslea (o null al desasignar).
    async _assignModulu(modulu, facultyId, facultyName) {
        this.state.loading = true;
        const affected = await this.orm.call(
            "op.faculty", "assign_perfilazio_modulu", [modulu.id, facultyId]);

        const idx = this.state.moduluak.findIndex(m => m.id === modulu.id);
        if (idx >= 0) {
            this.state.moduluak[idx].faculty_id = facultyId;
            this.state.moduluak[idx].faculty_name = facultyId ? facultyName : null;
        }

        // El profesor asignado puede estar o no en el panel izquierdo;
        // si está, actualizamos sus horas y resumen.
        for (const upd of affected) {
            const fidx = this.state.irakasleak.findIndex(f => f.id === upd.id);
            if (fidx >= 0) {
                this.state.irakasleak[fidx].orduak = upd.orduak;
                this.state.irakasleak[fidx].overload = upd.overload;
                this.state.irakasleak[fidx].gela = upd.gela;
                if (upd.pt_pes !== undefined) this.state.irakasleak[fidx].pt_pes = upd.pt_pes;
            }
            if (this.state.selectedFaculty && this.state.selectedFaculty.id === upd.id) {
                this.state.selectedFaculty.orduak = upd.orduak;
                this.state.selectedFaculty.overload = upd.overload;
                this.state.selectedFaculty.gela = upd.gela;
                if (upd.pt_pes !== undefined) this.state.selectedFaculty.pt_pes = upd.pt_pes;
            }
        }
        await this._refreshResumen();
        await this._refreshTaldeakLaburpena();
        this.state.loading = false;
    }

    async onSpecialIrakasleChange(ev, modulu) {
        const facultyId = parseInt(ev.target.value) || null;
        const cand = this.specialOptions(modulu).find(x => x.id === facultyId);
        await this._assignModulu(modulu, facultyId, cand ? cand.name : null);
    }

    // Módulos TUTO: asignar desde uno de los 3 desplegables (ORIENTA/LPO/INGELES).
    // Solo un profesor: al elegir en uno, los otros quedan en "—" automáticamente.
    async onTutoIrakasleChange(ev, modulu) {
        const facultyId = parseInt(ev.target.value) || null;
        let name = null;
        if (facultyId) {
            for (const dc of this.TUTO_DEPTS) {
                const f = (this.state.tutoIrakasleak[dc] || []).find(x => x.id === facultyId);
                if (f) { name = f.name; break; }
            }
        }
        await this._assignModulu(modulu, facultyId, name);
    }

    async clearPerfilazio(faculty) {
        if (!confirm(`"${faculty.name}"-ren perfilazio osoa hustu nahi duzu?`)) return;
        this.state.loading = true;
        const result = await this.orm.call("op.faculty", "clear_perfilazio_faculty", [faculty.id]);
        this._updateFacultyHours(faculty.id, result);
        await this._reloadModuluak();
        await this._refreshResumen();
        await this._refreshTaldeakLaburpena();
        this.state.loading = false;
    }

    async deleteImpersonal(faculty) {
        if (!confirm(`"${faculty.name}" ezabatu nahi duzu?`)) return;
        this.state.loading = true;
        await this.orm.call("op.faculty", "delete_perfilazio_impersonal", [faculty.id]);
        this.state.irakasleak = this.state.irakasleak.filter(f => f.id !== faculty.id);
        if (this.state.selectedFaculty && this.state.selectedFaculty.id === faculty.id) {
            this.state.selectedFaculty = null;
            this.state.karguak = [];
            this.state.addingKargu = false;
        }
        await this._reloadModuluak();
        this.state.loading = false;
    }

    async createImpersonal() {
        if (!this.state.selectedMintegi) return;
        this.state.loading = true;
        const faculty = await this.orm.call("op.faculty", "create_perfilazio_impersonal", [this.state.selectedMintegi.id]);
        this.state.irakasleak.push(faculty);
        await this._refreshResumen();
        this.state.loading = false;
    }

    async openAddKargu() {
        this.state.allKarguak = await this.orm.call(
            "op.faculty", "get_all_karguak", [this.state.selectedFaculty.id]);
        this.state.newKarguId = null;
        this.state.newKarguOrduak = 0;
        this.state.newKarguRemaining = 0;
        this.state.newKarguAllowZero = false;
        this.state.newKarguAllowDecimal = false;
        this.state.addingKargu = true;
    }

    onNewKarguSelect(ev) {
        this.state.newKarguId = parseInt(ev.target.value) || null;
        const k = this.state.allKarguak.find(x => x.id === this.state.newKarguId);
        this.state.newKarguRemaining = k ? k.remaining : 0;
        this.state.newKarguAllowZero = k ? !!k.allow_zero : false;
        this.state.newKarguAllowDecimal = k ? !!k.allow_decimal : false;
        this.state.newKarguOrduak = 0;
    }

    onNewKarguOrduak(ev) {
        this.state.newKarguOrduak = parseFloat(ev.target.value) || 0;
    }

    // [1, 2, ..., floor(max)] — opciones de horas enteras disponibles
    rangeOptions(max) {
        const n = Math.floor(max || 0);
        return Array.from({ length: n > 0 ? n : 0 }, (_, i) => i + 1);
    }

    // Opciones del desplegable al añadir un kargu nuevo (0 incluido si el
    // kargu admite 0h, p.ej. TUTO de cotutor sin RPT).
    newKarguOptions() {
        const opts = this.rangeOptions(this.state.newKarguRemaining);
        return this.state.newKarguAllowZero ? [0, ...opts] : opts;
    }

    // Opciones para una línea de kargu ya asignada (incluye su valor actual
    // y el 0 si el kargu admite 0h)
    rowKarguOptions(k) {
        const opts = this.rangeOptions(Math.max(k.max_orduak || 0, k.orduak || 0));
        return k.allow_zero ? [0, ...opts] : opts;
    }

    cancelAddKargu() {
        this.state.addingKargu = false;
    }

    async saveKargu() {
        if (!this.state.newKarguId || !this.state.selectedFaculty) return;
        // Permitir guardar 0h solo cuando el kargu lo admite (TUTO de cotutor)
        if (!this.state.newKarguOrduak && !this.state.newKarguAllowZero) return;
        const result = await this.orm.call("op.faculty", "upsert_perfilazio_kargu", [
            this.state.selectedFaculty.id,
            this.state.newKarguId,
            this.state.newKarguOrduak,
        ]);
        this.state.karguak = await this.orm.call("op.faculty", "get_perfilazio_karguak", [this.state.selectedFaculty.id]);
        this._updateFacultyHours(this.state.selectedFaculty.id, result);
        this.state.addingKargu = false;
        // Refrescar "Mintegiko karguak": las horas esleitzeke decrementan.
        await this._refreshTaldeakLaburpena();
    }

    async onKarguHoursChange(ev, kargu) {
        const orduak = parseFloat(ev.target.value) || 0;
        const result = await this.orm.call("op.faculty", "upsert_perfilazio_kargu", [
            this.state.selectedFaculty.id, kargu.kargu_id, orduak,
        ]);
        kargu.orduak = orduak;
        this._updateFacultyHours(this.state.selectedFaculty.id, result);
        await this._refreshTaldeakLaburpena();
    }

    async removeKargu(kargu) {
        const result = await this.orm.call("op.faculty", "delete_perfilazio_kargu", [kargu.id]);
        this.state.karguak = this.state.karguak.filter(k => k.id !== kargu.id);
        this._updateFacultyHours(this.state.selectedFaculty.id, result);
        await this._refreshTaldeakLaburpena();
    }

    async _refreshResumen() {
        const fid = this.state.selectedFaculty ? this.state.selectedFaculty.id : null;
        if (!fid) { this.state.resumenModuluak = []; return; }
        const rows = await this.orm.call("op.faculty", "get_perfilazio_resumen", [fid]);
        this.state.resumenModuluak = rows || [];
    }

    _updateFacultyHours(facultyId, result) {
        const fidx = this.state.irakasleak.findIndex(f => f.id === facultyId);
        if (fidx >= 0) {
            this.state.irakasleak[fidx].orduak = result.orduak;
            this.state.irakasleak[fidx].overload = result.overload;
            if (result.gela !== undefined) {
                this.state.irakasleak[fidx].gela = result.gela;
            }
        }
        if (this.state.selectedFaculty && this.state.selectedFaculty.id === facultyId) {
            this.state.selectedFaculty.orduak = result.orduak;
            this.state.selectedFaculty.overload = result.overload;
            if (result.gela !== undefined) {
                this.state.selectedFaculty.gela = result.gela;
            }
        }
    }

    // ── Laburpena (resumen del mintegi completo) ─────────────────────
    async openLaburpena() {
        if (!this.state.selectedMintegi) return;
        this.state.loading = true;
        const deptId = this.state.selectedMintegi.id;
        this.state.laburpenaData = await this.orm.call(
            "op.faculty", "get_perfilazio_laburpena", [deptId]);
        this.state.laburpenaOrdezkoak = await this.orm.call(
            "op.faculty", "get_perfilazio_ordezkoak", [deptId]);
        this.state.showLaburpena = true;
        this.state.loading = false;
    }

    closeLaburpena() {
        this.state.showLaburpena = false;
    }

    // Ordezkoak disponibles para un impersonal: los que NO están ya asignados
    // a OTRA plaza (una plaza = un profesor). El propio ordezkoa de lf se
    // mantiene para que se muestre como seleccionado.
    availableOrdezkoak(lf) {
        const taken = new Set(
            this.state.laburpenaData
                .filter(o => o.id !== lf.id && o.ordezko_esleitua_id)
                .map(o => o.ordezko_esleitua_id));
        return this.state.laburpenaOrdezkoak.filter(o => !taken.has(o.id));
    }

    // Anota qué ordezkoa del mintegi cubrirá una perfilación impersonal.
    async onLaburpenaOrdezkoChange(lf, ev) {
        const val = ev.target.value;
        const ordezkoId = val ? parseInt(val, 10) : false;
        const ok = await this.orm.call("op.faculty",
            "set_perfilazio_ordezko_esleitua", [lf.id, ordezkoId]);
        if (ok) {
            lf.ordezko_esleitua_id = ordezkoId;
        } else {
            ev.target.value = lf.ordezko_esleitua_id || "";
            this.notification.add(
                "Ordezko hori beste plaza batean esleituta dago.",
                { type: 'warning' });
        }
    }

    // ── Versiones de perfilación (snapshots por mintegi) ─────────────
    async toggleBertsioak() {
        this.state.showBertsioak = !this.state.showBertsioak;
        if (this.state.showBertsioak) await this._loadBertsioak();
    }

    async _loadBertsioak() {
        if (!this.state.selectedMintegi) return;
        this.state.bertsioak = await this.orm.call(
            "op.faculty", "get_perfilazio_bertsioak", [this.state.selectedMintegi.id]);
    }

    async saveBertsioa() {
        if (!this.state.selectedMintegi) return;
        const name = window.prompt(
            `"${this.state.selectedMintegi.name}" perfilazioaren bertsio-izena:`);
        if (!name || !name.trim()) return;
        this.state.loading = true;
        const v = await this.orm.call(
            "op.faculty", "save_perfilazio_bertsioa",
            [this.state.selectedMintegi.id, name.trim()]);
        this.state.loading = false;
        this.notification.add(`Gordeta: ${v.name}`, { type: 'success' });
        this.state.showBertsioak = true;
        await this._loadBertsioak();
    }

    async loadBertsioa(v) {
        if (!confirm(`"${v.name}" bertsioa kargatu? Uneko egoera ordeztuko da `
            + `(aldez aurretik automatikoki gordeko da).`)) return;
        this.state.loading = true;
        const res = await this.orm.call("op.faculty", "load_perfilazio_bertsioa", [v.id]);
        // Recargar toda la vista del mintegi
        await this._refreshIrakasleak();
        if (this.state.selectedBatch) await this._reloadModuluak();
        if (this.state.selectedFaculty) {
            this.state.karguak = await this.orm.call(
                "op.faculty", "get_perfilazio_karguak", [this.state.selectedFaculty.id]);
            await this._refreshResumen();
        }
        await this._refreshTaldeakLaburpena();
        await this._loadBertsioak();
        this.state.loading = false;
        const sk = res && res.skipped;
        const extra = sk && (sk.modules || sk.karguak || sk.faculty)
            ? ` (saltatuta: ${sk.modules} mod / ${sk.karguak} kargu / ${sk.faculty} irak.)` : '';
        this.notification.add(`Kargatuta: ${v.name}${extra}`, { type: 'success' });
    }

    async deleteBertsioa(v) {
        if (!confirm(`"${v.name}" bertsioa ezabatu?`)) return;
        await this.orm.call("op.faculty", "delete_perfilazio_bertsioa", [v.id]);
        this.state.bertsioak = this.state.bertsioak.filter(x => x.id !== v.id);
    }

    // Descarga una versión como fichero JSON portable (por códigos)
    async exportBertsioa(v) {
        const data = await this.orm.call(
            "op.faculty", "export_perfilazio_bertsioa", [v.id]);
        const blob = new Blob([JSON.stringify(data, null, 2)],
            { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `perfilazioa_${data.department || 'dept'}_${v.name}.json`
            .replace(/[^\w.\-]+/g, '_');
        a.click();
        URL.revokeObjectURL(url);
    }

    // Importa un fichero JSON de versión y crea una versión nueva en el mintegi
    async onImportFile(ev) {
        const file = ev.target.files && ev.target.files[0];
        ev.target.value = '';   // permitir reimportar el mismo fichero
        if (!file || !this.state.selectedMintegi) return;
        const text = await file.text();
        let parsed;
        try { parsed = JSON.parse(text); }
        catch (e) {
            this.notification.add('Fitxategi baliogabea (JSON okerra).', { type: 'danger' });
            return;
        }
        this.state.loading = true;
        let res;
        try {
            res = await this.orm.call("op.faculty", "import_perfilazio_bertsioa",
                [this.state.selectedMintegi.id, parsed]);
        } finally {
            this.state.loading = false;
        }
        this.state.showBertsioak = true;
        await this._loadBertsioak();
        const m = res.missing || {};
        const created = res.created_impersonal
            ? ` [${res.created_impersonal} impertsonal sortuta]` : '';
        const extra = (m.modules || m.karguak || m.faculty)
            ? ` (falta: ${m.modules || 0} mod / ${m.karguak || 0} kargu / ${m.faculty || 0} irak.)` : '';
        this.notification.add(`Inportatuta: ${res.name}${created}${extra}`, { type: 'success' });
    }

    // Nº de columnas de la rejilla ≈ raíz cuadrada (12 prof → 4 columnas → 4x3)
    laburpenaCols() {
        const n = this.state.laburpenaData.length;
        return n > 0 ? Math.ceil(Math.sqrt(n)) : 1;
    }

    formatH(h) {
        return Number.isFinite(h) ? h.toFixed(1) + 'h' : '0.0h';
    }

    // Perfilación completa: RPT exactamente en 17h (ni de menos ni overload).
    isComplete(f) {
        return !f.overload && Math.abs((f.orduak || 0) - 17) < 0.005;
    }

    _round(n) {
        return Math.round(n * 100) / 100;
    }

    _sumField(arr, field) {
        return this._round((arr || []).reduce((acc, x) => acc + (x[field] || 0), 0));
    }

    sumGela() {
        return this._sumField(this.state.resumenModuluak, 'gela_orduak');
    }

    sumRpt() {
        return this._round(
            this._sumField(this.state.resumenModuluak, 'rpt_total')
            + this._sumField(this.state.karguak, 'orduak')
        );
    }
}

registry.category("actions").add("perfilazioak_action", Perfilazioak);
