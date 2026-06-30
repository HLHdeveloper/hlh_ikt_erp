/** @odoo-module */
import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

class AulaEsleipena extends Component {
    static template = "openeducat_hernani.AulaEsleipena";
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
            gelak: [],        // columnas teoría (gela / gela_tailerra)
            tailerrak: [],    // columnas taller (tailerra / gela_tailerra)
            moduluak: [],     // lista plana (con _batch_id/_batch_name)
            loading: false,
        });
        onWillStart(async () => {
            this.state.mintegiak = await this.orm.call(
                "op.faculty", "get_perfilazio_mintegiak", []);
        });
    }

    async onMintegiChange(ev) {
        const id = parseInt(ev.target.value) || null;
        this.state.selectedMintegi = this.state.mintegiak.find(m => m.id === id) || null;
        this.state.selectedZikloa = null;
        this.state.selectedBatch = null;
        this.state.zikloak = [];
        this.state.batches = [];
        this.state.moduluak = [];
        this.state.gelak = [];
        this.state.tailerrak = [];
        if (!id) return;
        this.state.loading = true;
        const [zikloak, cols] = await Promise.all([
            this.orm.call("op.faculty", "get_perfilazio_zikloak", [id]),
            this.orm.call("op.subject", "get_aula_columns", [id]),
        ]);
        this.state.zikloak = zikloak;
        this.state.gelak = cols.gelak;
        this.state.tailerrak = cols.tailerrak;
        this.state.loading = false;
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
        await this._loadAllZikloModuluak();
        this.state.loading = false;
    }

    async onBatchChange(ev) {
        const id = parseInt(ev.target.value) || null;
        this.state.selectedBatch = this.state.batches.find(b => b.id === id) || null;
        if (!id) {
            // volver a mostrar todos los grupos del zikloa
            if (this.state.selectedZikloa) {
                this.state.loading = true;
                await this._loadAllZikloModuluak();
                this.state.loading = false;
            }
            return;
        }
        this.state.loading = true;
        const mods = await this.orm.call("op.subject", "get_aula_moduluak", [id]);
        mods.forEach(m => { m._batch_id = id; m._batch_name = this.state.selectedBatch.name; });
        this.state.moduluak = mods;
        this.state.loading = false;
    }

    async _loadAllZikloModuluak() {
        const batches = this.state.batches || [];
        const lists = await Promise.all(
            batches.map(b => this.orm.call("op.subject", "get_aula_moduluak", [b.id]))
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
    }

    // Grupos a renderizar (una card por taldea)
    moduluakGroups() {
        if (this.state.selectedBatch) {
            return [{ key: 'batch', batch_name: this.state.selectedBatch.name, items: this.state.moduluak }];
        }
        if (this.state.selectedZikloa) {
            const byId = {}, groups = [];
            for (const b of (this.state.batches || [])) {
                const g = { key: b.id, batch_name: b.name, items: [] };
                byId[b.id] = g; groups.push(g);
            }
            for (const m of this.state.moduluak) {
                const g = byId[m._batch_id];
                if (g) g.items.push(m);
            }
            return groups.filter(g => g.items.length);
        }
        return [];
    }

    has(mod, kind, classroomId) {
        const arr = kind === "teoria" ? mod.teoria_ids : mod.tailerra_ids;
        return arr.includes(classroomId);
    }

    async toggle(mod, kind, classroomId) {
        const now = await this.orm.call("op.subject", "toggle_aula", [mod.id, classroomId, kind]);
        const arr = kind === "teoria" ? mod.teoria_ids : mod.tailerra_ids;
        const idx = arr.indexOf(classroomId);
        if (now && idx === -1) { arr.push(classroomId); }
        else if (!now && idx !== -1) { arr.splice(idx, 1); }
    }

    noAula(mod) {
        return mod.teoria_ids.length === 0 && mod.tailerra_ids.length === 0;
    }

    // Estado de una columna de aula en un grupo (card): 'all' | 'some' | 'none'
    colState(group, kind, classroomId) {
        const items = group.items || [];
        if (!items.length) return 'none';
        const n = items.filter(m => this.has(m, kind, classroomId)).length;
        return n === 0 ? 'none' : (n === items.length ? 'all' : 'some');
    }

    // Clic en cabecera de aula: asigna a TODOS los módulos del grupo; si ya la
    // tienen todos, la quita.
    async toggleColumn(group, kind, classroomId) {
        const items = group.items || [];
        if (!items.length) return;
        const value = this.colState(group, kind, classroomId) !== 'all';
        await this.orm.call("op.subject", "set_aula_column",
            [items.map(m => m.id), classroomId, kind, value]);
        for (const m of items) {
            const arr = kind === "teoria" ? m.teoria_ids : m.tailerra_ids;
            const idx = arr.indexOf(classroomId);
            if (value && idx === -1) { arr.push(classroomId); }
            else if (!value && idx !== -1) { arr.splice(idx, 1); }
        }
    }
}

registry.category("actions").add("aula_esleipena_action", AulaEsleipena);
