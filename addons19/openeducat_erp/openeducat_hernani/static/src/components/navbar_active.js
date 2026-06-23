/** @odoo-module */
// Resalta en la barra de menú horizontal el apartado activo (clase
// `o_nav_active` sobre la entrada cuyo data-section = menu_id). Odoo no marca
// la sección activa de forma nativa.
//
// IMPORTANTE sobre la señal de navegación: al pinchar un apartado, Odoo navega
// con `history.pushState` (router_service, debounced). pushState NO dispara el
// `hashchange` nativo NI el evento `ROUTE_CHANGE` (que solo se emite en
// hashchange real —atrás/adelante— y al refrescar). Por eso un simple listener
// de hashchange/ROUTE_CHANGE solo se actualizaba al refrescar.
// Solución: fijamos el id activo directamente en `onNavBarDropdownItemSelection`
// (se llama en cada clic de apartado) y mantenemos ROUTE_CHANGE + onMounted como
// respaldo para atrás/adelante, URL directa y refresco.
import { NavBar } from "@web/webclient/navbar/navbar";
import { patch } from "@web/core/utils/patch";
import { onMounted, onPatched, onWillUnmount } from "@odoo/owl";

function menuIdFromHash() {
    const m = (window.location.hash || "").match(/menu_id=(\d+)/);
    return m ? parseInt(m[1]) : null;
}

patch(NavBar.prototype, {
    setup() {
        super.setup();
        this._activeMenuId = menuIdFromHash();
        this._onRouteChange = () => {
            this._activeMenuId = menuIdFromHash();
            this._applyActiveSection();
        };
        this.env.bus.addEventListener("ROUTE_CHANGE", this._onRouteChange);
        onWillUnmount(() => {
            this.env.bus.removeEventListener("ROUTE_CHANGE", this._onRouteChange);
        });
        onMounted(() => this._applyActiveSection());
        onPatched(() => this._applyActiveSection());
    },

    onNavBarDropdownItemSelection(menu) {
        super.onNavBarDropdownItemSelection(menu);
        if (menu) {
            // pushState es debounced: el hash aún no refleja el nuevo menu_id,
            // por eso usamos el id del menú pulsado en vez de leer el hash.
            this._activeMenuId = menu.id;
            this._applyActiveSection();
        }
    },

    _applyActiveSection() {
        const root = this.root && this.root.el;
        if (!root) return;
        const menuId = this._activeMenuId;
        for (const el of root.querySelectorAll(".o_menu_sections [data-section]")) {
            const sec = parseInt(el.getAttribute("data-section"));
            el.classList.toggle("o_nav_active", menuId !== null && sec === menuId);
        }
    },
});
