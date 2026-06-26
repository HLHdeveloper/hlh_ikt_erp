/** @odoo-module */
import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

const MODEL = "op.fet.room.unavailability";

class FetRoomUnavail extends Component {
    static template = "openeducat_hernani.FetRoomUnavail";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.state = useState({
            solairuak: [],
            gelak: [],
            days: [],
            timings: [],
            selectedSolairua: "",   // "" = todas las plantas
            selectedRoom: null,
            unavail: {},
        });

        onWillStart(async () => {
            const [solairuak, grid, gelak] = await Promise.all([
                this.orm.call(MODEL, "get_solairuak", []),
                this.orm.call(MODEL, "get_grid", []),
                this.orm.call(MODEL, "get_gelak", [null]),
            ]);
            this.state.solairuak = solairuak;
            this.state.days = grid.days;
            this.state.timings = grid.timings;
            this.state.gelak = gelak;
        });
    }

    async onSolairuaChange(ev) {
        const key = ev.target.value || null;
        this.state.selectedSolairua = key || "";
        this.state.selectedRoom = null;
        this.state.unavail = {};
        this.state.gelak = await this.orm.call(MODEL, "get_gelak", [key]);
    }

    async selectRoom(r) {
        this.state.selectedRoom = r;
        const keys = await this.orm.call(MODEL, "get_unavailability", [r.id]);
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
        const r = this.state.selectedRoom;
        if (!r) {
            return;
        }
        const now = await this.orm.call(MODEL, "toggle_slot", [
            r.id, dayKey, timingId,
        ]);
        const key = this.cellKey(dayKey, timingId);
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

registry.category("actions").add("fet_room_unavail_action", FetRoomUnavail);
