/** @odoo-module */
import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

const CARD_LABELS = {
    total: "Irakasleak",
    funtzionarioa: "Funtzionarioak",
    ordezkoa: "Ordezkoak",
    bajan: "Bajan daudenak",
    karguak: "Karguak",
};

class SisDashboard extends Component {
    static template = "openeducat_hernani.SisDashboard";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({
            counts: { total: 0, funtzionarioak: 0, ordezkoak: 0, bajan: 0, karguak: 0 },
            activeCard: null,
            drillTitle: "",
            deptBreakdown: [],
            selectedDept: null,
            // karguak drill-down
            karguTypes: [],
            selectedKarguType: null,
            // bajan drill-down
            selectedBajanFaculty: null,
            bajanHistory: [],
            // shared faculty list
            facultyList: [],
            loading: false,
        });
        onWillStart(() => this.loadCounts());
    }

    get showDrilldown() {
        return !!this.state.activeCard;
    }

    async loadCounts() {
        const counts = await this.orm.call("op.faculty", "get_dashboard_counts", []);
        Object.assign(this.state.counts, counts);
    }

    _resetDrill() {
        this.state.deptBreakdown = [];
        this.state.selectedDept = null;
        this.state.karguTypes = [];
        this.state.selectedKarguType = null;
        this.state.selectedBajanFaculty = null;
        this.state.bajanHistory = [];
        this.state.facultyList = [];
    }

    async onCardClick(cardType) {
        if (this.state.activeCard === cardType) {
            this.state.activeCard = null;
            this._resetDrill();
            return;
        }
        this.state.activeCard = cardType;
        this._resetDrill();
        this.state.drillTitle = CARD_LABELS[cardType] + " — mintegika";
        this.state.loading = true;
        if (cardType === "bajan") {
            this.state.deptBreakdown = await this.orm.call("op.faculty", "get_bajan_depts", []);
        } else if (cardType === "karguak") {
            this.state.deptBreakdown = await this.orm.call("op.faculty", "get_kargu_depts", []);
        } else {
            const kidergoa = cardType === "total" ? null : cardType;
            this.state.deptBreakdown = await this.orm.call(
                "op.faculty", "get_dept_breakdown", [kidergoa]
            );
        }
        this.state.loading = false;
    }

    async onDeptClick(dept) {
        this.state.selectedDept = dept;
        this.state.loading = true;
        if (this.state.activeCard === "bajan") {
            this.state.facultyList = await this.orm.call(
                "op.faculty", "get_bajan_faculty_by_dept", [dept.id]
            );
        } else if (this.state.activeCard === "karguak") {
            this.state.karguTypes = await this.orm.call(
                "op.faculty", "get_kargu_types_for_dept", [dept.id]
            );
        } else {
            const kidergoa = this.state.activeCard === "total" ? null : this.state.activeCard;
            this.state.facultyList = await this.orm.call(
                "op.faculty", "get_faculty_by_dept", [dept.id, kidergoa]
            );
        }
        this.state.loading = false;
    }

    async onKarguTypeClick(ktype) {
        this.state.selectedKarguType = ktype;
        this.state.loading = true;
        this.state.facultyList = await this.orm.call(
            "op.faculty", "get_faculty_for_dept_kargu",
            [this.state.selectedDept.id, ktype.code]
        );
        this.state.loading = false;
    }

    async onBajanTitularClick(faculty) {
        this.state.selectedBajanFaculty = faculty;
        this.state.loading = true;
        this.state.bajanHistory = await this.orm.call(
            "op.faculty", "get_bajan_history", [faculty.id]
        );
        this.state.loading = false;
    }

    backToDepts() {
        this.state.selectedDept = null;
        this.state.karguTypes = [];
        this.state.selectedKarguType = null;
        this.state.selectedBajanFaculty = null;
        this.state.bajanHistory = [];
        this.state.facultyList = [];
    }

    backToKarguTypes() {
        this.state.selectedKarguType = null;
        this.state.facultyList = [];
    }

    backToBajanFaculty() {
        this.state.selectedBajanFaculty = null;
        this.state.bajanHistory = [];
    }

    async onBukatuOrdezkapen(h) {
        await this.orm.call("op.ordezkapen", "action_bukatu", [[h.id]]);
        this.state.loading = true;
        this.state.bajanHistory = await this.orm.call(
            "op.faculty", "get_bajan_history", [this.state.selectedBajanFaculty.id]
        );
        await this.loadCounts();
        this.state.loading = false;
    }

    async onFacultyClick(faculty) {
        await this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "op.faculty",
            res_id: faculty.id,
            views: [[false, "form"]],
            target: "current",
        });
    }
}

registry.category("actions").add("sis_dashboard_action", SisDashboard);
