/** @odoo-module */
import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

const MODEL = "op.fet.teacher.unavailability";

class FetTeacherUnavail extends Component {
    static template = "openeducat_hernani.FetTeacherUnavail";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.state = useState({
            mintegiak: [],
            irakasleak: [],
            days: [],
            timings: [],
            selectedMintegi: null,
            selectedFaculty: null,
            // Set de claves "day|timing_id" marcadas como NO disponible
            unavail: {},
        });

        onWillStart(async () => {
            const [mintegiak, grid] = await Promise.all([
                this.orm.call(MODEL, "get_mintegiak", []),
                this.orm.call(MODEL, "get_grid", []),
            ]);
            this.state.mintegiak = mintegiak;
            this.state.days = grid.days;
            this.state.timings = grid.timings;
        });
    }

    async onMintegiChange(ev) {
        const id = parseInt(ev.target.value, 10) || null;
        this.state.selectedMintegi = id;
        this.state.selectedFaculty = null;
        this.state.unavail = {};
        this.state.irakasleak = id
            ? await this.orm.call(MODEL, "get_irakasleak", [id])
            : [];
    }

    async selectFaculty(f) {
        this.state.selectedFaculty = f;
        const keys = await this.orm.call(MODEL, "get_unavailability", [f.id]);
        const map = {};
        for (const k of keys) {
            map[k] = true;
        }
        this.state.unavail = map;
    }

    cellKey(dayKey, timingId) {
        return `${dayKey}|${timingId}`;
    }

    isUnavail(dayKey, timingId) {
        return !!this.state.unavail[this.cellKey(dayKey, timingId)];
    }

    async toggleCell(dayKey, timingId) {
        const f = this.state.selectedFaculty;
        if (!f) {
            return;
        }
        const now = await this.orm.call(MODEL, "toggle_slot", [
            f.id, dayKey, timingId,
        ]);
        const key = this.cellKey(dayKey, timingId);
        // Reasignar el objeto para forzar la reactividad de OWL
        const map = { ...this.state.unavail };
        if (now) {
            map[key] = true;
        } else {
            delete map[key];
        }
        this.state.unavail = map;
    }

    unavailCount() {
        return Object.keys(this.state.unavail).length;
    }
}

registry.category("actions").add("fet_teacher_unavail_action", FetTeacherUnavail);
