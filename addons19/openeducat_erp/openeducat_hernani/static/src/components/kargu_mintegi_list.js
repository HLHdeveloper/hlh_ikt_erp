/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { listView } from "@web/views/list/list_view";
import { ListController } from "@web/views/list/list_controller";

/**
 * Lista de líneas de reparto (op.kargu.mintegi) usada en el menú Karguak.
 * El botón "Berria" (Nuevo) NO crea una línea: abre la ficha del cargo
 * (op.kargu form), donde se asigna el cargo a cualquier mintegi en la
 * pestaña "Perfilazio Irakasleak".
 */
export class KarguMintegiListController extends ListController {
    setup() {
        super.setup();
        this.action = useService("action");
    }

    /** Tras cerrar la ficha del cargo: refrescar la lista Y el panel lateral
     *  (searchpanel), para que un mintegi recién asignado aparezca al instante.
     *  `_notify()` refetchea las secciones del searchpanel (tienen
     *  enable_counters) y dispara el "update" que recarga los registros;
     *  `_reset()` no borra los filtros activos del usuario. */
    async _afterFormClose() {
        const sm = this.env.searchModel;
        if (sm && typeof sm._notify === "function") {
            await sm._notify();
        } else {
            await this.model.root.load();
        }
    }

    async createRecord() {
        return this.action.doAction(
            "openeducat_hernani.act_open_op_kargu_new",
            { onClose: () => this._afterFormClose() }
        );
    }

    /** Clic en una fila: abrir la ficha del cargo (op.kargu), no la fila
     *  de solo lectura de la vista SQL. */
    openRecord(record) {
        const kargu = record.data.kargu_id;
        const karguId = Array.isArray(kargu) ? kargu[0] : kargu;
        if (!karguId) {
            return;
        }
        return this.action.doAction(
            {
                type: "ir.actions.act_window",
                res_model: "op.kargu",
                res_id: karguId,
                views: [[false, "form"]],
                target: "current",
            },
            { onClose: () => this._afterFormClose() }
        );
    }
}

registry.category("views").add("kargu_mintegi_list", {
    ...listView,
    Controller: KarguMintegiListController,
});
