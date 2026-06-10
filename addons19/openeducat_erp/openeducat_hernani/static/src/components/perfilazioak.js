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

            resumenModuluak: [],

            ingelesaMode: false,

            showLaburpena: false,
            laburpenaData: [],

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
        if (!this.state.selectedZikloa) return;
        this.state.loading = true;
        this.state.zikloModuluak = await this.orm.call(
            "op.faculty", "get_perfilazio_ziklo_moduluak", [this.state.selectedZikloa.id]);
        this.state.loading = false;
    }

    // La selección refleja qué módulos YA tienen su copia (HE_/DESDO_) creada
    _initKopiaSelection() {
        const flag = this._activeKopiaFlag();
        const sel = {};
        for (const m of this.state.zikloModuluak) sel[m.id] = !!m[flag];
        this.state.selectedKopiak = sel;
    }

    async _refreshKopiaPanel() {
        if (!this.isKopiakActive()) {
            this.state.zikloModuluak = [];
            this.state.selectedKopiak = {};
            return;
        }
        if (!this.state.zikloModuluak.length) await this._ensureZikloModuluak();
        this._initKopiaSelection();
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
        const res = await this.orm.call(
            "op.faculty", "toggle_perfilazio_kopia", [modulu.id, prefix]);
        const flag = this._activeKopiaFlag();
        const zm = this.state.zikloModuluak.find(x => x.id === modulu.id);
        if (zm) zm[flag] = res.exists;
        this.state.selectedKopiak[modulu.id] = res.exists;
        this._recomputeZikloIndicator();
        // Al crear/eliminar una copia puede cambiar la perfilación de algún
        // profesor (si la copia estaba asignada): recargar moduluak, irakasleak
        // y resumen para recalcular horas.
        if (this.state.selectedBatch) await this._reloadModuluak();
        await this._refreshIrakasleak();
        await this._refreshResumen();
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
        this._resetApoyo();

        if (!id) return;
        this.state.loading = true;
        this.state.moduluak = await this.orm.call("op.faculty", "get_perfilazio_moduluak", [id]);
        await this._loadSpecialIrakasleak();
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
            }
            if (this.state.selectedFaculty && this.state.selectedFaculty.id === upd.id) {
                this.state.selectedFaculty.orduak = upd.orduak;
                this.state.selectedFaculty.overload = upd.overload;
                this.state.selectedFaculty.gela = upd.gela;
            }
        }
        await this._refreshResumen();
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
            }
            if (this.state.selectedFaculty && this.state.selectedFaculty.id === upd.id) {
                this.state.selectedFaculty.orduak = upd.orduak;
                this.state.selectedFaculty.overload = upd.overload;
                this.state.selectedFaculty.gela = upd.gela;
            }
        }
        await this._refreshResumen();
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
        this.state.addingKargu = true;
    }

    onNewKarguSelect(ev) {
        this.state.newKarguId = parseInt(ev.target.value) || null;
        const k = this.state.allKarguak.find(x => x.id === this.state.newKarguId);
        this.state.newKarguRemaining = k ? k.remaining : 0;
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

    // Opciones para una línea de kargu ya asignada (incluye su valor actual)
    rowKarguOptions(k) {
        return this.rangeOptions(Math.max(k.max_orduak || 0, k.orduak || 0));
    }

    cancelAddKargu() {
        this.state.addingKargu = false;
    }

    async saveKargu() {
        if (!this.state.newKarguId || !this.state.selectedFaculty || !this.state.newKarguOrduak) return;
        const result = await this.orm.call("op.faculty", "upsert_perfilazio_kargu", [
            this.state.selectedFaculty.id,
            this.state.newKarguId,
            this.state.newKarguOrduak,
        ]);
        this.state.karguak = await this.orm.call("op.faculty", "get_perfilazio_karguak", [this.state.selectedFaculty.id]);
        this._updateFacultyHours(this.state.selectedFaculty.id, result);
        this.state.addingKargu = false;
    }

    async onKarguHoursChange(ev, kargu) {
        const orduak = parseFloat(ev.target.value) || 0;
        const result = await this.orm.call("op.faculty", "upsert_perfilazio_kargu", [
            this.state.selectedFaculty.id, kargu.kargu_id, orduak,
        ]);
        kargu.orduak = orduak;
        this._updateFacultyHours(this.state.selectedFaculty.id, result);
    }

    async removeKargu(kargu) {
        const result = await this.orm.call("op.faculty", "delete_perfilazio_kargu", [kargu.id]);
        this.state.karguak = this.state.karguak.filter(k => k.id !== kargu.id);
        this._updateFacultyHours(this.state.selectedFaculty.id, result);
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
        this.state.laburpenaData = await this.orm.call(
            "op.faculty", "get_perfilazio_laburpena", [this.state.selectedMintegi.id]);
        this.state.showLaburpena = true;
        this.state.loading = false;
    }

    closeLaburpena() {
        this.state.showLaburpena = false;
    }

    // Nº de columnas de la rejilla ≈ raíz cuadrada (12 prof → 4 columnas → 4x3)
    laburpenaCols() {
        const n = this.state.laburpenaData.length;
        return n > 0 ? Math.ceil(Math.sqrt(n)) : 1;
    }

    formatH(h) {
        return Number.isFinite(h) ? h.toFixed(1) + 'h' : '0.0h';
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

    sumZorretan() {
        return this._sumField(this.state.resumenModuluak, 'orduak_zorretan');
    }

    sumRpt() {
        return this._round(
            this._sumField(this.state.resumenModuluak, 'rpt_total')
            + this._sumField(this.state.karguak, 'orduak')
        );
    }
}

registry.category("actions").add("perfilazioak_action", Perfilazioak);
