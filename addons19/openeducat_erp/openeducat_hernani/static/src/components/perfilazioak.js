/** @odoo-module */
import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

class Perfilazioak extends Component {
    static template = "openeducat_hernani.Perfilazioak";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.state = useState({
            mintegiak: [],
            zikloak: [],
            batches: [],
            selectedMintegi: null,
            selectedZikloa: null,
            selectedBatch: null,

            irakasleak: [],
            moduluak: [],

            selectedFaculty: null,
            karguak: [],

            addingKargu: false,
            allKarguak: [],
            newKarguId: null,
            newKarguOrduak: 0,
            newKarguRemaining: 0,

            resumenModuluak: [],

            ingelesaMode: false,

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
        this.state.irakasleak = [];
        this.state.selectedFaculty = null;
        this.state.karguak = [];
        this.state.addingKargu = false;
        this.state.ingelesaMode = false;

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
    }

    async onZikloaChange(ev) {
        const id = parseInt(ev.target.value) || null;
        this.state.selectedZikloa = this.state.zikloak.find(z => z.id === id) || null;
        this.state.selectedBatch = null;
        this.state.batches = [];
        this.state.moduluak = [];

        if (!id) return;
        this.state.loading = true;
        this.state.batches = await this.orm.call("op.faculty", "get_perfilazio_batches", [id]);
        this.state.loading = false;
    }

    async onBatchChange(ev) {
        const id = parseInt(ev.target.value) || null;
        this.state.selectedBatch = this.state.batches.find(b => b.id === id) || null;
        this.state.moduluak = [];

        if (!id) return;
        this.state.loading = true;
        this.state.moduluak = await this.orm.call("op.faculty", "get_perfilazio_moduluak", [id]);
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
