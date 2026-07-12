/** @odoo-module **/
import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

class EsgDashboard extends Component {
    static template = "esg_management.EsgDashboard";
    static props = {};

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({
            departments: [],
            totalCO2: 0,
            totalXP: 0,
            recentTransactions: [],
            loading: true,
        });
        onWillStart(async () => {
            await this.loadDashboardData();
        });
    }

    async loadDashboardData() {
        try {
            const [depts, xpData] = await Promise.all([
                this.orm.searchRead(
                    "hr.department",
                    [],
                    ["name", "environmental_score", "social_score", "governance_score", "total_score", "carbon_budget", "carbon_used"],
                    { limit: 50 }
                ),
                this.orm.searchRead(
                    "esg.xp.transaction",
                    [],
                    ["employee_id", "xp_amount", "transaction_type", "date"],
                    { limit: 100, order: "date desc" }
                ),
            ]);

            this.state.departments = depts;
            this.state.totalCO2 = depts.reduce((sum, d) => sum + (d.carbon_used || 0), 0);
            this.state.totalXP = xpData.reduce((sum, t) => sum + (t.xp_amount || 0), 0);
            this.state.recentTransactions = xpData.slice(0, 10);
        } catch (e) {
            console.error("ESG Dashboard load error:", e);
        } finally {
            this.state.loading = false;
        }
    }

    getScoreClass(score) {
        if (score >= 70) return "score-good";
        if (score >= 40) return "score-medium";
        return "score-poor";
    }

    safeFixed(val, digits = 1) {
        const n = parseFloat(val);
        return isNaN(n) ? "0.0" : n.toFixed(digits);
    }

    navigateTo(model, viewType) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: model,
            view_mode: viewType,
            views: [[false, viewType]],
        });
    }
}

registry.category("actions").add("esg_dashboard", EsgDashboard);
