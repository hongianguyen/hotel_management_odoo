# -*- coding: utf-8 -*-
# ResortPro 19 - Night Audit Logic (NEW per Blueprint)
# Called by ir.cron every night to consolidate daily revenue
from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)


class NightAudit(models.Model):
    """Night Audit model: stores daily revenue snapshots.
    Populated by the ir.cron job 'action_run_night_audit'.
    """
    _name = 'night.audit'
    _description = 'ResortPro Night Audit'
    _order = 'audit_date desc'
    _rec_name = 'audit_date'

    audit_date = fields.Date(
        string="Audit Date",
        default=fields.Date.today,
        required=True,
        help="Date for which this audit was run",
    )
    total_rooms = fields.Integer(string="Total Rooms", readonly=True)
    occupied_rooms = fields.Integer(string="Occupied Rooms", readonly=True)
    available_rooms = fields.Integer(string="Available Rooms", readonly=True)
    new_checkins = fields.Integer(string="Check-Ins Today", readonly=True)
    new_checkouts = fields.Integer(string="Check-Outs Today", readonly=True)
    revenue_today = fields.Monetary(string="Revenue Today", readonly=True, currency_field='currency_id')
    revenue_total = fields.Monetary(string="Total Revenue (All Time)", readonly=True, currency_field='currency_id')
    pending_payment = fields.Monetary(string="Pending Payments", readonly=True, currency_field='currency_id')
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        default=lambda self: self.env.company.currency_id,
        readonly=True,
    )
    notes = fields.Text(string="Audit Notes", help="Automatic notes from the audit run")

    @api.model
    def action_run_night_audit(self):
        """
        Entry point called by ir.cron at end of each business day.
        Computes revenue and room statistics, creates a NightAudit record.
        """
        today = fields.Date.today()
        _logger.info("ResortPro Night Audit: running for %s", today)

        # --- Room statistics ---
        RoomProduct = self.env['product.template']
        total_rooms = RoomProduct.search_count([('is_room', '=', True)])
        occupied_rooms = RoomProduct.search_count([('is_room', '=', True), ('status', '=', 'occupied')])
        available_rooms = RoomProduct.search_count([('is_room', '=', True), ('status', '=', 'available')])

        # --- Booking events today ---
        Booking = self.env['room.booking']
        new_checkins = Booking.search_count([('state', '=', 'check_in')])
        new_checkouts = Booking.search_count([('state', '=', 'check_out')])

        # --- Financial snapshot ---
        revenue_today = 0.0
        revenue_total = 0.0
        pending_payment = 0.0
        Move = self.env['account.move']
        for move in Move.search([('move_type', '=', 'out_invoice')]):
            if not (move.ref and 'BOOKING' in move.ref):
                continue
            if move.payment_state == 'paid':
                revenue_total += move.amount_total
                if move.date == today:
                    revenue_today += move.amount_total
            elif move.payment_state == 'not_paid':
                pending_payment += move.amount_total

        # --- Create audit record ---
        audit = self.create({
            'audit_date': today,
            'total_rooms': total_rooms,
            'occupied_rooms': occupied_rooms,
            'available_rooms': available_rooms,
            'new_checkins': new_checkins,
            'new_checkouts': new_checkouts,
            'revenue_today': round(revenue_today, 2),
            'revenue_total': round(revenue_total, 2),
            'pending_payment': round(pending_payment, 2),
            'notes': _(
                "Night Audit completed automatically at end of %(date)s. "
                "Rooms: %(total)s total / %(occupied)s occupied / %(avail)s available.",
                date=today,
                total=total_rooms,
                occupied=occupied_rooms,
                avail=available_rooms,
            ),
        })
        _logger.info("ResortPro Night Audit completed. ID=%s", audit.id)
        return True
