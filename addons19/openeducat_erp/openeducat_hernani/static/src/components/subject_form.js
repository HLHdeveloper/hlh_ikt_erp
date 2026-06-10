/** @odoo-module */
import { registry } from "@web/core/registry";
import { formView } from "@web/views/form/form_view";
import { FormController } from "@web/views/form/form_controller";

// Formulario de op.subject: al pulsar "Gorde" (icono de disquete) guarda y,
// si el guardado es correcto, vuelve a la lista anterior (que conserva el
// filtro/búsqueda activos, igual que pulsar la migaja de pan "Moduluak").
export class SubjectSaveBackFormController extends FormController {
    async saveButtonClicked(params = {}) {
        const saved = await super.saveButtonClicked(params);
        if (saved && this.env.config.historyBack) {
            this.env.config.historyBack();
        }
        return saved;
    }
}

registry.category("views").add("subject_save_back_form", {
    ...formView,
    Controller: SubjectSaveBackFormController,
});
