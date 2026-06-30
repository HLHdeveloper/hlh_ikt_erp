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
        this.action = useService("action");
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
            // Profesores de departamentos transversales (INGELES/ORIENTA/LPO)
            // ofrecidos en cualquier mintegi bajo "Irakasle Tronkalak".
            tronkalIrakasleak: [],
            moduluak: [],
            // Candidatos por departamento para módulos especiales (no técnicos)
            specialIrakasleak: {},
            // Candidatos (ORIENTA/LPO/INGELES) para módulos TUTO
            tutoIrakasleak: {},

            // Apoyo Educativo (solo ciclos OLH*): grupos I/II/III con tope RPT
            apoyoKodea: '',
            apoyoData: { id: null, guztira_orduak: 0, sum_rpt: 0, modules: [] },
            apoyoNew: { code: '', pt_pes: '', orduak: 0, kurtsoa: '',
                        banaketa_id: '', gela_orduak: 0, rpt_total: 0, orduak_zorretan: 0 },
            banaketaAukerak: [],

            selectedFaculty: null,
            karguak: [],

            addingKargu: false,
            // Selector de añadir kargu activo: 'kudeaketa' (KARGUAK) o
            // 'ardurak' (ARDURAK). Hay un selector separado para cada mota.
            addingKarguMota: null,
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

            showPlazak: false,
            plazakData: [],

            showBertsioak: false,
            bertsioak: [],

            taldeakLaburpena: [],
            mintegiKarguak: [],
            eleanitzaLaburpena: {
                eleanitza: { total: 0, pending: 0 },
                desdoblea: { total: 0, pending: 0 },
            },
            plazakOrduak: {
                PES: { lekt: 0, ez_lekt: 0 },
                PT: { lekt: 0, ez_lekt: 0 },
            },

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
        this.state.tronkalIrakasleak = [];
        this.state.selectedFaculty = null;
        this.state.karguak = [];
        this.state.addingKargu = false;
        this.state.ingelesaMode = false;
        this.state.showLaburpena = false;
        this.state.laburpenaData = [];
        this.state.showPlazak = false;
        this.state.plazakData = [];
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
        await this._loadTronkalIrakasleak();
        await this._refreshTaldeakLaburpena();
        this.state.loading = false;
    }

    // Carga los profesores tronkales (INGELES/ORIENTA/LPO) del mintegi actual,
    // excluidos los que ya pertenecen a él (los devuelve el servidor filtrados).
    async _loadTronkalIrakasleak() {
        if (!this.state.selectedMintegi) {
            this.state.tronkalIrakasleak = [];
            return;
        }
        this.state.tronkalIrakasleak = await this.orm.call(
            "op.faculty", "get_perfilazio_tronkal_irakasleak",
            [this.state.selectedMintegi.id]);
    }

    // Busca un profesor por id en la lista del mintegi o en la de tronkalak,
    // para reflejar en vivo los cambios de horas/gela/overload en ambas.
    _findIrakasle(id) {
        return this.state.irakasleak.find(f => f.id === id)
            || this.state.tronkalIrakasleak.find(f => f.id === id)
            || null;
    }

    async _reloadModuluak() {
        if (this.state.ingelesaMode) {
            this.state.moduluak = await this.orm.call("op.faculty", "get_perfilazio_ingelesa_moduluak", []);
            await this._loadSpecialIrakasleak();
        } else if (this.state.selectedBatch) {
            this.state.moduluak = await this.orm.call("op.faculty", "get_perfilazio_moduluak", [this.state.selectedBatch.id]);
            await this._loadSpecialIrakasleak();
        } else if (this.state.selectedZikloa) {
            await this._loadAllZikloModuluak();
        }
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
        this._resetApoyo();

        if (!id) return;
        this.state.loading = true;
        this.state.batches = await this.orm.call("op.faculty", "get_perfilazio_batches", [id]);
        // Sin taldea seleccionada: mostrar los módulos de TODOS los grupos del
        // zikloa, agrupados por taldea (cards apiladas).
        await this._loadAllZikloModuluak();
        this.state.loading = false;
    }

    // Carga en state.moduluak (lista plana que usan los handlers de
    // asignación) los módulos de TODOS los grupos del zikloa, etiquetando cada
    // módulo con _batch_id/_batch_name para poder agruparlos en la vista.
    async _loadAllZikloModuluak() {
        const batches = this.state.batches || [];
        const lists = await Promise.all(
            batches.map(b => this.orm.call("op.faculty", "get_perfilazio_moduluak", [b.id]))
        );
        const all = [];
        batches.forEach((b, i) => {
            for (const m of lists[i]) {
                m._batch_id = b.id;
                m._batch_name = b.name;
                all.push(m);
            }
        });
        this.state.moduluak = all;
        await this._loadSpecialIrakasleak();
    }

    // Grupos a renderizar en el panel Moduluak (una card por grupo):
    //  - Ingelesa o taldea concreta → 1 grupo con state.moduluak.
    //  - Zikloa sin taldea → un grupo por cada taldea del zikloa.
    moduluakGroups() {
        if (this.state.ingelesaMode) {
            return [{ key: 'ingelesa', batch_name: 'INGELESA — guztiak', items: this.state.moduluak }];
        }
        if (this.state.selectedBatch) {
            return [{ key: 'batch', batch_name: this.state.selectedBatch.name, items: this.state.moduluak }];
        }
        if (this.state.selectedZikloa) {
            return this.moduluakByBatch().map(g => ({ key: g.batch_id, ...g }));
        }
        return [];
    }

    // Agrupa state.moduluak por taldea (en el orden de state.batches), para
    // renderizar una card de Moduluak por grupo cuando hay zikloa sin taldea.
    moduluakByBatch() {
        const byId = {};
        const groups = [];
        for (const b of (this.state.batches || [])) {
            const g = { batch_id: b.id, batch_name: b.name, items: [] };
            byId[b.id] = g;
            groups.push(g);
        }
        for (const m of this.state.moduluak) {
            const g = byId[m._batch_id];
            if (g) g.items.push(m);
        }
        return groups.filter(g => g.items.length);
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
        if (!this.state.selectedMintegi) {
            this.state.taldeakLaburpena = [];
            this.state.mintegiKarguak = [];
            this.state.eleanitzaLaburpena = {
                eleanitza: { total: 0, pending: 0 },
                desdoblea: { total: 0, pending: 0 },
            };
            this.state.plazakOrduak = {
                PES: { lekt: 0, ez_lekt: 0 },
                PT: { lekt: 0, ez_lekt: 0 },
            };
            return;
        }
        this.state.taldeakLaburpena = await this.orm.call(
            "op.faculty", "get_perfilazio_taldeak_laburpena",
            [this.state.selectedMintegi.id]);
        this.state.mintegiKarguak = await this.orm.call(
            "op.faculty", "get_perfilazio_mintegi_karguak",
            [this.state.selectedMintegi.id]);
        this.state.eleanitzaLaburpena = await this.orm.call(
            "op.faculty", "get_perfilazio_eleanitza_laburpena",
            [this.state.selectedMintegi.id]);
        this.state.plazakOrduak = await this.orm.call(
            "op.faculty", "get_perfilazio_plazak_laburpena",
            [this.state.selectedMintegi.id]);
    }

    // ORDU EZ LEKTIBOAK = Mintegiko karguak GUZTIRA + Eleanitza/Desdobleak GUZTIRA.
    orduEzLektiboak() {
        const e = this.state.eleanitzaLaburpena;
        const t = this.mintegiKarguakGuztira()
            + (e.eleanitza.total || 0) + (e.desdoblea.total || 0);
        return Math.round(t * 100) / 100;
    }

    // GUZTIRA de la tabla Eleanitza / Desdobleak.
    eleanitzaGuztira(field) {
        const e = this.state.eleanitzaLaburpena;
        return Math.round(((e.eleanitza[field] || 0) + (e.desdoblea[field] || 0)) * 100) / 100;
    }

    // GUZTIRA de "Mintegiko karguak": suma de una columna ('total' = ordu
    // guztiak por defecto; 'pending' = esleitzeke orduak).
    mintegiKarguakGuztira(field = 'total') {
        const t = this.state.mintegiKarguak.reduce((s, mk) => s + (mk[field] || 0), 0);
        return Math.round(t * 100) / 100;
    }

    // "Mintegiko karguak" dividido por kargu_mota: KARGUAK (kudeaketa) y
    // ARDURAK (ardurak). La tabla se muestra en dos secciones separadas.
    get mintegiKudeaketak() {
        return this.state.mintegiKarguak.filter((mk) => mk.kargu_mota === 'kudeaketa');
    }

    get mintegiArdurak() {
        return this.state.mintegiKarguak.filter((mk) => mk.kargu_mota !== 'kudeaketa');
    }

    // GUZTIRA de una lista concreta de karguak (una sección).
    karguakZerrendaGuztira(list, field = 'total') {
        const t = (list || []).reduce((s, mk) => s + (mk[field] || 0), 0);
        return Math.round(t * 100) / 100;
    }

    // Plazen laburpena: por distintivo PT/PES de los profesores, suma sus
    // horas y las convierte a plazas (17h = 1; 6h=1/3, 9h=1/2, 12h=2/3).
    plazakLaburpena() {
        const po = this.state.plazakOrduak;
        return ['PES', 'PT'].map(cat => {
            const lekt = Math.round((po[cat].lekt || 0) * 100) / 100;
            const ez = Math.round((po[cat].ez_lekt || 0) * 100) / 100;
            const total = Math.round((lekt + ez) * 100) / 100;
            return { cat, lekt, ez, total, label: this._plazaLabel(total) };
        });
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
        this._resetApoyo();

        if (!id) {
            // Sin taldea: volver a mostrar los módulos de todos los grupos.
            if (this.state.selectedZikloa) {
                this.state.loading = true;
                await this._loadAllZikloModuluak();
                this.state.loading = false;
            }
            return;
        }
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
        this.state.karguak = await this.orm.call("op.faculty", "get_perfilazio_karguak",
            [faculty.id, this.state.selectedMintegi?.id]);
        await this._refreshResumen();
    }

    // Alterna manualmente el distintivo PT/PES del profesor (persistente).
    async togglePtPes(f) {
        const val = await this.orm.call("op.faculty", "toggle_perfilazio_pt_pes", [f.id]);
        f.pt_pes = val;
        if (this.state.selectedFaculty && this.state.selectedFaculty.id === f.id) {
            this.state.selectedFaculty.pt_pes = val;
        }
        // El distintivo cambia el reparto lektiboak/ez-lektiboak de "Plazen laburpena".
        await this._refreshTaldeakLaburpena();
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
            const f = this._findIrakasle(upd.id);
            if (f) {
                f.orduak = upd.orduak;
                f.overload = upd.overload;
                f.gela = upd.gela;
                if (upd.pt_pes !== undefined) f.pt_pes = upd.pt_pes;
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
            const f = this._findIrakasle(upd.id);
            if (f) {
                f.orduak = upd.orduak;
                f.overload = upd.overload;
                f.gela = upd.gela;
                if (upd.pt_pes !== undefined) f.pt_pes = upd.pt_pes;
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

    // Desasignar un módulo desde la tabla "Perfilazio Laburpena": lo libera
    // (faculty_id = null) para que quede disponible para otro profesor.
    async unassignResumenModulu(rm) {
        if (!rm || !rm.id) return;
        this.state.loading = true;
        const affected = await this.orm.call(
            "op.faculty", "assign_perfilazio_modulu", [rm.id, false]);
        // Reflejar en la lista de módulos de la derecha si está cargado allí.
        const idx = this.state.moduluak.findIndex(m => m.id === rm.id);
        if (idx >= 0) {
            this.state.moduluak[idx].faculty_id = null;
            this.state.moduluak[idx].faculty_name = null;
        }
        for (const upd of affected) {
            const f = this._findIrakasle(upd.id);
            if (f) {
                f.orduak = upd.orduak;
                f.overload = upd.overload;
                f.gela = upd.gela;
                if (upd.pt_pes !== undefined) f.pt_pes = upd.pt_pes;
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

    async openAddKargu(mota) {
        this.state.allKarguak = await this.orm.call(
            "op.faculty", "get_all_karguak",
            [this.state.selectedFaculty.id, this.state.selectedMintegi?.id]);
        this.state.newKarguId = null;
        this.state.newKarguOrduak = 0;
        this.state.newKarguRemaining = 0;
        this.state.newKarguAllowZero = false;
        this.state.newKarguAllowDecimal = false;
        this.state.addingKarguMota = mota || 'ardurak';
        this.state.addingKargu = true;
    }

    // Karguak disponibles para añadir, filtrados por mota: KARGUAK
    // (kudeaketa) o ARDURAK (ardurak). Cada selector usa su propia lista.
    allKarguakByMota(mota) {
        if (mota === 'kudeaketa') {
            return this.state.allKarguak.filter((k) => k.kargu_mota === 'kudeaketa');
        }
        return this.state.allKarguak.filter((k) => k.kargu_mota !== 'kudeaketa');
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
        this.state.addingKarguMota = null;
    }

    async saveKargu() {
        if (!this.state.newKarguId || !this.state.selectedFaculty) return;
        // Permitir guardar 0h solo cuando el kargu lo admite (TUTO de cotutor)
        if (!this.state.newKarguOrduak && !this.state.newKarguAllowZero) return;
        const result = await this.orm.call("op.faculty", "upsert_perfilazio_kargu", [
            this.state.selectedFaculty.id,
            this.state.newKarguId,
            this.state.newKarguOrduak,
            this.state.selectedMintegi?.id,
        ]);
        this.state.karguak = await this.orm.call("op.faculty", "get_perfilazio_karguak",
            [this.state.selectedFaculty.id, this.state.selectedMintegi?.id]);
        this._updateFacultyHours(this.state.selectedFaculty.id, result);
        this.state.addingKargu = false;
        this.state.addingKarguMota = null;
        // Refrescar "Mintegiko karguak": las horas esleitzeke decrementan.
        await this._refreshTaldeakLaburpena();
    }

    async onKarguHoursChange(ev, kargu) {
        const orduak = parseFloat(ev.target.value) || 0;
        const result = await this.orm.call("op.faculty", "upsert_perfilazio_kargu", [
            this.state.selectedFaculty.id, kargu.kargu_id, orduak,
            this.state.selectedMintegi?.id,
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
        const f = this._findIrakasle(facultyId);
        if (f) {
            f.orduak = result.orduak;
            f.overload = result.overload;
            if (result.gela !== undefined) {
                f.gela = result.gela;
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

    // Descarga la "Perfilazio laburpena" del mintegi en PDF (informe QWeb
    // server-side; el mintegi va en active_ids del contexto).
    async downloadLaburpenaPdf() {
        if (!this.state.selectedMintegi) return;
        await this.action.doAction(
            "openeducat_hernani.action_report_perfilazio_laburpena",
            { additionalContext: {
                active_ids: [this.state.selectedMintegi.id],
                active_model: "op.department",
            } });
    }

    // ── Plazak (tabla de plazas/vacantes del mintegi) ────────────────
    async openPlazak() {
        if (!this.state.selectedMintegi) return;
        this.state.loading = true;
        this.state.plazakData = await this.orm.call(
            "op.faculty", "get_perfilazio_plazak", [this.state.selectedMintegi.id]);
        this.state.showPlazak = true;
        this.state.loading = false;
    }

    closeViews() {
        this.state.showLaburpena = false;
        this.state.showPlazak = false;
    }

    // Guarda en vivo las columnas editables (BAKANTEA / OHARRAK) de una plaza.
    async onPlazaFieldChange(plaza, field, ev) {
        const value = ev.target.value;
        await this.orm.call("op.faculty", "set_perfilazio_plaza",
            [plaza.id, field, value]);
        plaza[field] = value;
    }

    // Exporta la tabla de plazas a CSV (separador ';' por las comas decimales).
    exportPlazakCsv() {
        const cols = [
            ['izena', 'IZENA'], ['pt_pes', 'PT/PES'], ['taldea', 'TALDEA'],
            ['jardunaldi_mota', 'JARDUNALDI_MOTA'], ['hizkuntza_perfila', 'HIZKUNTZA_PERFILA'],
            ['plazaren_informazioa', 'PLAZAREN INFORMAZIOA'], ['jarduna', 'JARDUNA'],
            ['bakantea', 'BAKANTEA'], ['oharrak', 'OHARRAK'],
        ];
        const esc = (v) => '"' + String(v ?? '').replace(/"/g, '""') + '"';
        const sep = ';';
        const lines = [cols.map(c => esc(c[1])).join(sep)];
        for (const p of this.state.plazakData) {
            lines.push(cols.map(c => esc(p[c[0]])).join(sep));
        }
        // BOM para que Excel reconozca UTF-8 (eñes, tildes, euskera).
        const blob = new Blob(['﻿' + lines.join('\r\n')],
            { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `plazak_${this.state.selectedMintegi?.name || 'mintegi'}.csv`
            .replace(/[^\w.\-]+/g, '_');
        a.click();
        URL.revokeObjectURL(url);
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
        await this._loadTronkalIrakasleak();
        if (this.state.selectedBatch) await this._reloadModuluak();
        if (this.state.selectedFaculty) {
            this.state.karguak = await this.orm.call(
                "op.faculty", "get_perfilazio_karguak",
                [this.state.selectedFaculty.id, this.state.selectedMintegi?.id]);
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
