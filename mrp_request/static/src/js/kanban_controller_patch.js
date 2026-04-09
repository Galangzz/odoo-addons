/** @odoo-module **/

import { ProductCatalogKanbanController } from '@product/product_catalog/kanban_controller';
import { patch } from '@web/core/utils/patch';
import { _t } from '@web/core/l10n/translation';

patch(ProductCatalogKanbanController.prototype, {
    _defineButtonContent() {
        if (this.orderResModel === 'mrp.request.request') {
            this.buttonString = _t('Back to Request');
        } else {
            super._defineButtonContent();
        }
    },
});
