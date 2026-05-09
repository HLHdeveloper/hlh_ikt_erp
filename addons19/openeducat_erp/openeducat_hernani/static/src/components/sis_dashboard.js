/** @odoo-module */
import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

const CARD_LABELS = {
    total: "Irakasleak",
    funtzionarioa: "Funtzionarioak",
    ordezkoa: "Ordezkoak",
};

class SisDashboard extends Component {
    static template = "openeducat_hernani.SisDashboard";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({
            counts: { total: 0, funtzionarioak: 0, ordezkoak: 0, bajan: 0 },
            activeCard: null,
            drillTitle: "",
            deptBreakdown: [],
            selectedDept: null,
            facultyList: [],
            loading: false,
        });
        onWillStart(() => this.loadCounts());
    }

    get showDrilldown() {
        return this.state.activeCard && this.state.activeCard !== "bajan";
    }

    async loadCounts() {
        const counts = await this.orm.call("op.faculty", "get_dashboard_counts", []);
        Object.assign(this.state.counts, counts);
    }

    async onCardClick(cardType) {
        if (cardType === "bajan") {
            await this.action.doAction("openeducat_hernani.act_open_op_ordezkapen_view");
            return;
        }
        if (this.state.activeCard === cardType) {
            this.state.activeCard = null;
            this.state.deptBreakdown = [];
            this.state.selectedDept = null;
            this.state.facultyList = [];
            return;
        }
        this.state.activeCard = cardType;
        this.state.selectedDept = null;
        this.state.facultyList = [];
        this.state.drillTitle = CARD_LABELS[cardType] + " — mintegika";
        this.state.loading = true;
        const kidergoa = cardType === "total" ? null : cardType;
        this.state.deptBreakdown = await this.orm.call(
            "op.faculty", "get_dept_breakdown", [kidergoa]
        );
        this.state.loading = false;
    }

    async onDeptClick(dept) {
        this.state.selectedDept = dept;
        this.state.loading = true;
        const kidergoa = this.state.activeCard === "total" ? null : this.state.activeCard;
        this.state.facultyList = await this.orm.call(
            "op.faculty", "get_faculty_by_dept", [dept.id, kidergoa]
        );
        this.state.loading = false;
    }

    backToDepts() {
        this.state.selectedDept = null;
        this.state.facultyList = [];
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
