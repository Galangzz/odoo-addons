/** @odoo-module **/

import { registry } from "@web/core/registry";
import { browser } from "@web/core/browser";
import { useService } from "@web/core/utils/hooks";
import { Component } from "@odoo/owl";

const cogMenuRegistry = registry.category("cogMenu");

class MrpReportCogItem extends Component {
    setup() {
        this.actionService = useService("action");
    }

    async _onClick() {
        // Panggil action report berdasarkan XML ID yang Anda buat sebelumnya
        return this.actionService.doAction("mrp_request.action_report_mrp_production");
    }
}

// Template untuk tampilan di dalam dropdown
MrpReportCogItem.template = "mrp_request.MrpReportCogItem";

// Registrasi ke dalam CogMenu
export const mrpReportCogItem = {
    Component: MrpReportCogItem,
    groupNumber: 20, // Agar muncul di bawah Export (Export biasanya group 10)
    isStateless: true,
    // Filter agar tombol hanya muncul di model mrp.production
    condition: (env) => env.config.resModel === "mrp.production",
};

cogMenuRegistry.add("mrp-report-cog-item", mrpReportCogItem);