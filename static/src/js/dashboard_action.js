/** @odoo-module */
/**
 * ResortPro 19 - Hotel Dashboard
 * Migrated from Cybrosys Hotel Management v18 → Odoo 19 OWL component
 *
 * Changes from v18:
 * - owl imported from "@odoo/owl" (Odoo 19 standard)
 * - rpc() replaced with this.orm.call() for method calls
 * - State stored in reactive object (useState)
 * - Template uses t-out instead of t-esc for HTML safety
 */
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, useState } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";

// Today's date in YYYY-M-D format (for domain filters)
const today = new Date();
const formattedDate = `${today.getFullYear()}-${today.getMonth() + 1}-${today.getDate()}`;

export class CustomDashBoard extends Component {
    static template = "hotel_management_odoo.CustomDashBoard";

    setup() {
        this.action = useService("action");
        this.orm = useService("orm");
        // Reactive state: all dashboard counters
        this.state = useState({
            total_room: 0,
            available_room: 0,
            staff: 0,
            check_in: 0,
            reservation: 0,
            check_out: 0,
            total_vehicle: 0,
            available_vehicle: 0,
            total_event: 0,
            today_events: 0,
            pending_events: 0,
            food_items: 0,
            food_order: 0,
            total_revenue: "0",
            today_revenue: "0",
            pending_payment: "0",
        });
        onWillStart(() => this._fetchData());
    }

    /**
     * Fetch dashboard statistics from the server via ORM service.
     * Odoo 19: use this.orm.call() instead of legacy rpc().
     */
    async _fetchData() {
        const result = await this.orm.call("room.booking", "get_details", [{}], {});
        const sym = result.currency_symbol || "";
        const pos = result.currency_position || "after";

        const formatAmount = (amount) =>
            pos === "before" ? `${sym} ${amount}` : `${amount} ${sym}`;

        Object.assign(this.state, {
            total_room: result.total_room,
            available_room: result.available_room,
            staff: result.staff,
            check_in: result.check_in,
            reservation: result.reservation,
            check_out: result.check_out,
            total_vehicle: result.total_vehicle,
            available_vehicle: result.available_vehicle,
            total_event: result.total_event,
            today_events: result.today_events,
            pending_events: result.pending_events,
            food_items: result.food_items,
            food_order: result.food_order,
            total_revenue: formatAmount(result.total_revenue),
            today_revenue: formatAmount(result.today_revenue),
            pending_payment: formatAmount(result.pending_payment),
        });
    }

    // ── Action helpers ──────────────────────────────────────────────────
    _doAction(name, res_model, domain = [], extra = {}) {
        this.action.doAction({
            name: _t(name),
            type: "ir.actions.act_window",
            res_model,
            view_mode: "list,form",
            views: [[false, "list"], [false, "form"]],
            domain,
            target: "current",
            ...extra,
        });
    }

    total_rooms(ev) {
        ev.stopPropagation();
        this._doAction("Rooms", "product.template", [["is_room", "=", true]]);
    }
    check_ins(ev) {
        ev.stopPropagation();
        this._doAction("Check-In", "room.booking", [["state", "=", "check_in"]]);
    }
    available_rooms(ev) {
        ev.stopPropagation();
        this._doAction("Available Rooms", "product.template", [
            ["is_room", "=", true], ["status", "=", "available"],
        ]);
    }
    reservations(ev) {
        ev.stopPropagation();
        this._doAction("Total Reservations", "room.booking", [["state", "=", "reserved"]]);
    }
    check_outs(ev) {
        this._doAction("Today's Check-Out", "room.booking", [
            ["room_line_ids.checkout_date", "=", formattedDate],
        ]);
    }
    fetch_total_staff(ev) {
        ev.stopPropagation();
        this._doAction("Total Staff", "res.users", [
            ["groups_id.name", "in", [
                "Admin", "Cleaning Team User", "Cleaning Team Head",
                "Receptionist", "Maintenance Team User", "Maintenance Team Leader",
            ]],
        ]);
    }
    fetch_total_vehicle(ev) {
        ev.stopPropagation();
        this._doAction("Total Vehicles", "fleet.vehicle.model", []);
    }
    async fetch_available_vehicle(ev) {
        ev.stopPropagation();
        const result = await this.orm.call("fleet.booking.line", "search_available_vehicle", [{}], {});
        this._doAction("Available Vehicles", "fleet.vehicle.model", [["id", "not in", result]]);
    }
    view_total_events(ev) {
        ev.stopPropagation();
        this.action.doAction({
            name: _t("Total Events"),
            type: "ir.actions.act_window",
            res_model: "event.event",
            view_mode: "kanban,list,form",
            views: [[false, "kanban"], [false, "list"], [false, "form"]],
            domain: [],
            target: "current",
        });
    }
    fetch_today_events(ev) {
        ev.stopPropagation();
        this.action.doAction({
            name: _t("Today's Events"),
            type: "ir.actions.act_window",
            res_model: "event.event",
            view_mode: "kanban,list,form",
            views: [[false, "kanban"], [false, "list"], [false, "form"]],
            domain: [["date_end", "=", formattedDate]],
            target: "current",
        });
    }
    fetch_pending_events(ev) {
        ev.stopPropagation();
        this.action.doAction({
            name: _t("Pending Events"),
            type: "ir.actions.act_window",
            res_model: "event.event",
            view_mode: "kanban,list,form",
            views: [[false, "kanban"], [false, "list"], [false, "form"]],
            domain: [["date_end", ">=", formattedDate]],
            target: "current",
        });
    }
    fetch_food_item(ev) {
        ev.stopPropagation();
        this._doAction("Food Items", "lunch.product", []);
    }
    async fetch_food_order(ev) {
        ev.stopPropagation();
        const result = await this.orm.call("food.booking.line", "search_food_orders", [{}], {});
        this._doAction("Food Orders", "food.booking.line", [["id", "in", result]]);
    }
}

registry.category("actions").add("custom_dashboard_tags", CustomDashBoard);
