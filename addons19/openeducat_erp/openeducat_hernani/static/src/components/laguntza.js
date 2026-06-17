/** @odoo-module */
import { registry } from "@web/core/registry";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { Component } from "@odoo/owl";

// Carpeta estática donde build_html.py deja los manuales en HTML.
const BASE = "/openeducat_hernani/static/manualak/";

// Ítem de systray "LAGUNTZA": despliega los manuales y los abre en pestaña nueva.
export class LaguntzaMenu extends Component {
    openManual(file) {
        window.open(BASE + file, "_blank");
    }
}
LaguntzaMenu.template = "openeducat_hernani.LaguntzaMenu";
LaguntzaMenu.components = { Dropdown, DropdownItem };

export const systrayItem = { Component: LaguntzaMenu };
// sequence 26 → a la izquierda del icono de mensajes (sequence 25).
registry.category("systray").add("openeducat_hernani.laguntza", systrayItem, { sequence: 26 });
