# -*- coding: utf-8 -*-
# ResortPro 19 - Migrated from Cybrosys Hotel Management v18
# Key fix: pytz imported directly (not from odoo.tools.safe_eval)
# Python 3.12 compatible datetime handling
from datetime import datetime, timedelta
import pytz
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class RoomBooking(models.Model):
    """Core hotel booking model (Folio) for ResortPro 19.
    Handles check-in, check-out, invoicing and Night Audit.
    """
    _name = "room.booking"
    _description = "Hotel Room Booking (Folio)"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    # ─────────────────────────── IDENTIFICATION ────────────────────────────
    name = fields.Char(
        string="Folio Number", readonly=True, index=True,
        copy=False, default="New",
        help="Auto-generated folio reference number",
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string="Company", required=True, index=True,
        default=lambda self: self.env.company,
        help="Company processing this booking",
    )

    # ─────────────────────────── PARTNER ───────────────────────────────────
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string="Customer", required=True, index=True, tracking=1,
        domain="[('type', '!=', 'private'), ('company_id', 'in', (False, company_id))]",
        help="Guest / customer for this booking",
    )
    user_id = fields.Many2one(
        comodel_name='res.partner',
        string="Invoice Address",
        compute='_compute_user_id',
        required=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        help="Invoice address (auto-computed from partner)",
    )

    # ─────────────────────────── DATES ─────────────────────────────────────
    date_order = fields.Datetime(
        string="Order Date", required=True, copy=False,
        default=fields.Datetime.now,
        help="Date the booking was created",
    )
    checkin_date = fields.Datetime(
        string="Check In", help="Expected check-in date",
        default=fields.Datetime.now,
    )
    checkout_date = fields.Datetime(
        string="Check Out", help="Expected check-out date",
        default=lambda self: fields.Datetime.now() + timedelta(hours=23, minutes=59, seconds=59),
    )
    duration = fields.Integer(
        string="Duration in Days",
        help="Number of nights (auto-computed from check-in/check-out)",
    )
    duration_visible = fields.Float(string="Duration", help="Display helper for duration")

    # ─────────────────────────── STATUS FLAGS ──────────────────────────────
    is_checkin = fields.Boolean(default=False, string="Is Checked In")
    maintenance_request_sent = fields.Boolean(
        default=False, string="Maintenance Sent",
        help="True after a maintenance request has been sent for this booking",
    )
    invoice_button_visible = fields.Boolean(
        string='Invoice Button Visible', copy=False,
        help="Show invoice button in the view",
    )

    # ─────────────────────────── POLICY & PAYMENT ──────────────────────────
    hotel_policy = fields.Selection(
        selection=[
            ("prepaid", "On Booking"),
            ("manual", "On Check In"),
            ("picking", "On Checkout"),
        ],
        default="manual", string="Hotel Policy",
        help="When payment is expected from the guest",
        tracking=True,
    )
    invoice_status = fields.Selection(
        selection=[
            ('no_invoice', 'Nothing To Invoice'),
            ('to_invoice', 'To Invoice'),
            ('invoiced', 'Invoiced'),
        ],
        string="Invoice Status",
        default='no_invoice', copy=False, tracking=True,
        help="Current invoicing status of this booking",
    )
    hotel_invoice_id = fields.Many2one(
        comodel_name="account.move",
        string="Invoice", copy=False,
        help="Invoice generated for this booking",
    )
    invoice_count = fields.Integer(
        compute='_compute_invoice_count',
        string="Invoice Count",
        help="Number of invoices linked to this booking",
    )
    account_move = fields.Integer(string='Invoice Id', help="ID of the linked invoice")

    # ─────────────────────────── PRICELIST / CURRENCY ──────────────────────
    pricelist_id = fields.Many2one(
        comodel_name='product.pricelist',
        string="Pricelist",
        compute='_compute_pricelist_id',
        store=True, readonly=False, required=True, tracking=1,
        help="Pricelist used to compute room and service prices",
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string="Currency",
        related='pricelist_id.currency_id',
        depends=['pricelist_id.currency_id'],
        help="Currency from the pricelist",
    )

    # ─────────────────────────── STATE ─────────────────────────────────────
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('reserved', 'Reserved'),
            ('check_in', 'Check In'),
            ('check_out', 'Check Out'),
            ('cancel', 'Cancelled'),
            ('done', 'Done'),
        ],
        string='State', default='draft', tracking=True, copy=False,
        help="Current lifecycle state of the booking",
    )

    # ─────────────────────────── SERVICE FLAGS ─────────────────────────────
    need_service = fields.Boolean(default=False, string="Need Service")
    need_fleet = fields.Boolean(default=False, string="Need Vehicle")
    need_food = fields.Boolean(default=False, string="Need Food")
    need_event = fields.Boolean(default=False, string="Need Event")

    # ─────────────────────────── ONE2MANY LINES ────────────────────────────
    room_line_ids = fields.One2many(
        comodel_name="room.booking.line", inverse_name="booking_id",
        string="Room Lines",
        help="Individual room bookings in this folio",
    )
    service_line_ids = fields.One2many(
        comodel_name="service.booking.line", inverse_name="booking_id",
        string="Services",
        help="Additional hotel services",
    )
    food_order_line_ids = fields.One2many(
        comodel_name="food.booking.line", inverse_name="booking_id",
        string="Food Orders",
        help="Food and beverage orders",
    )
    vehicle_line_ids = fields.One2many(
        comodel_name="fleet.booking.line", inverse_name="booking_id",
        string="Vehicles",
        help="Vehicle bookings",
    )
    event_line_ids = fields.One2many(
        comodel_name="event.booking.line", inverse_name="booking_id",
        string="Events",
        help="Event bookings",
    )

    # ─────────────────────────── MONETARY TOTALS ───────────────────────────
    amount_untaxed = fields.Monetary(string="Untaxed Total", store=True, compute='_compute_amount_untaxed', tracking=5)
    amount_tax = fields.Monetary(string="Tax Total", store=True, compute='_compute_amount_untaxed')
    amount_total = fields.Monetary(string="Total", store=True, compute='_compute_amount_untaxed', tracking=4)

    amount_untaxed_room = fields.Monetary(string="Room Subtotal", compute='_compute_amount_untaxed', tracking=5)
    amount_untaxed_food = fields.Monetary(string="Food Subtotal", compute='_compute_amount_untaxed', tracking=5)
    amount_untaxed_event = fields.Monetary(string="Event Subtotal", compute='_compute_amount_untaxed', tracking=5)
    amount_untaxed_service = fields.Monetary(string="Service Subtotal", compute='_compute_amount_untaxed', tracking=5)
    amount_untaxed_fleet = fields.Monetary(string="Fleet Subtotal", compute='_compute_amount_untaxed', tracking=5)

    amount_taxed_room = fields.Monetary(string="Room Tax", compute='_compute_amount_untaxed', tracking=5)
    amount_taxed_food = fields.Monetary(string="Food Tax", compute='_compute_amount_untaxed', tracking=5)
    amount_taxed_event = fields.Monetary(string="Event Tax", compute='_compute_amount_untaxed', tracking=5)
    amount_taxed_service = fields.Monetary(string="Service Tax", compute='_compute_amount_untaxed', tracking=5)
    amount_taxed_fleet = fields.Monetary(string="Fleet Tax", compute='_compute_amount_untaxed', tracking=5)

    amount_total_room = fields.Monetary(string="Room Total", compute='_compute_amount_untaxed', tracking=5)
    amount_total_food = fields.Monetary(string="Food Total", compute='_compute_amount_untaxed', tracking=5)
    amount_total_event = fields.Monetary(string="Event Total", compute='_compute_amount_untaxed', tracking=5)
    amount_total_service = fields.Monetary(string="Service Total", compute='_compute_amount_untaxed', tracking=5)
    amount_total_fleet = fields.Monetary(string="Fleet Total", compute='_compute_amount_untaxed', tracking=5)

    # ═══════════════════════════ CRUD ══════════════════════════════════════

    @api.model_create_multi
    def create(self, vals_list):
        """Generate folio sequence on creation."""
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('room.booking') or 'New'
        return super().create(vals_list)

    # ═══════════════════════════ COMPUTES ══════════════════════════════════

    @api.depends('partner_id')
    def _compute_user_id(self):
        """Compute invoice address from partner."""
        for order in self:
            order.user_id = (
                order.partner_id.address_get(['invoice'])['invoice']
                if order.partner_id else False
            )

    def _compute_invoice_count(self):
        """Count invoices referencing this folio number."""
        for record in self:
            record.invoice_count = self.env['account.move'].search_count(
                [('ref', '=', record.name)]
            )

    @api.depends('partner_id')
    def _compute_pricelist_id(self):
        """Compute pricelist from partner."""
        for order in self:
            if not order.partner_id:
                order.pricelist_id = False
                continue
            order = order.with_company(order.company_id)
            order.pricelist_id = order.partner_id.property_product_pricelist

    @api.depends(
        'room_line_ids.price_subtotal', 'room_line_ids.price_tax', 'room_line_ids.price_total',
        'food_order_line_ids.price_subtotal', 'food_order_line_ids.price_tax', 'food_order_line_ids.price_total',
        'service_line_ids.price_subtotal', 'service_line_ids.price_tax', 'service_line_ids.price_total',
        'vehicle_line_ids.price_subtotal', 'vehicle_line_ids.price_tax', 'vehicle_line_ids.price_total',
        'event_line_ids.price_subtotal', 'event_line_ids.price_tax', 'event_line_ids.price_total',
    )
    def _compute_amount_untaxed(self, flag=False):
        """Aggregate totals from all booking lines and return invoice-ready list."""
        for rec in self:
            room_lines = rec.room_line_ids
            food_lines = rec.food_order_line_ids
            service_lines = rec.service_line_ids
            fleet_lines = rec.vehicle_line_ids
            event_lines = rec.event_line_ids

            rec.amount_untaxed_room = sum(room_lines.mapped('price_subtotal'))
            rec.amount_taxed_room = sum(room_lines.mapped('price_tax'))
            rec.amount_total_room = sum(room_lines.mapped('price_total'))

            rec.amount_untaxed_food = sum(food_lines.mapped('price_subtotal'))
            rec.amount_taxed_food = sum(food_lines.mapped('price_tax'))
            rec.amount_total_food = sum(food_lines.mapped('price_total'))

            rec.amount_untaxed_service = sum(service_lines.mapped('price_subtotal'))
            rec.amount_taxed_service = sum(service_lines.mapped('price_tax'))
            rec.amount_total_service = sum(service_lines.mapped('price_total'))

            rec.amount_untaxed_fleet = sum(fleet_lines.mapped('price_subtotal'))
            rec.amount_taxed_fleet = sum(fleet_lines.mapped('price_tax'))
            rec.amount_total_fleet = sum(fleet_lines.mapped('price_total'))

            rec.amount_untaxed_event = sum(event_lines.mapped('price_subtotal'))
            rec.amount_taxed_event = sum(event_lines.mapped('price_tax'))
            rec.amount_total_event = sum(event_lines.mapped('price_total'))

            rec.amount_untaxed = (
                rec.amount_untaxed_room + rec.amount_untaxed_food
                + rec.amount_untaxed_service + rec.amount_untaxed_fleet
                + rec.amount_untaxed_event
            )
            rec.amount_tax = (
                rec.amount_taxed_room + rec.amount_taxed_food
                + rec.amount_taxed_service + rec.amount_taxed_fleet
                + rec.amount_taxed_event
            )
            rec.amount_total = (
                rec.amount_total_room + rec.amount_total_food
                + rec.amount_total_service + rec.amount_total_fleet
                + rec.amount_total_event
            )

        # Build invoice line list (used by action_invoice)
        booking_list = []
        if flag:
            # fetch existing invoice lines to avoid duplicates
            existing = self.env['account.move.line'].search_read(
                domain=[('ref', '=', self.name), ('display_type', '!=', 'payment_term')],
                fields=['name', 'quantity', 'price_unit', 'product_type'],
            )
            existing_keys = {(r['name'], r['price_unit'], r['product_type']) for r in existing}

            for line in self.room_line_ids:
                key = (line.room_id.name, line.price_unit, 'room')
                if key not in existing_keys:
                    booking_list.append({
                        'name': line.room_id.name,
                        'quantity': line.uom_qty,
                        'price_unit': line.price_unit,
                        'product_type': 'room',
                    })
                    line.booking_line_visible = True

            for line in self.food_order_line_ids:
                booking_list.append(self._build_line_dict(line, 'food', line.food_id.name))
            for line in self.service_line_ids:
                booking_list.append(self._build_line_dict(line, 'service', line.service_id.name))
            for line in self.vehicle_line_ids:
                booking_list.append(self._build_line_dict(line, 'fleet', line.fleet_id.name))
            for line in self.event_line_ids:
                booking_list.append(self._build_line_dict(line, 'event', line.event_id.name))

        return booking_list

    def _build_line_dict(self, line, product_type, name):
        """Helper: build invoice line dictionary from a booking line."""
        return {
            'name': name,
            'quantity': line.uom_qty,
            'price_unit': line.price_unit,
            'product_type': product_type,
        }

    # ═══════════════════════════ ONCHANGE ══════════════════════════════════

    @api.onchange('need_food')
    def _onchange_need_food(self):
        if not self.need_food:
            self.food_order_line_ids = [(5, 0, 0)]

    @api.onchange('need_service')
    def _onchange_need_service(self):
        if not self.need_service:
            self.service_line_ids = [(5, 0, 0)]

    @api.onchange('need_fleet')
    def _onchange_need_fleet(self):
        if not self.need_fleet:
            self.vehicle_line_ids = [(5, 0, 0)]

    @api.onchange('need_event')
    def _onchange_need_event(self):
        if not self.need_event:
            self.event_line_ids = [(5, 0, 0)]

    @api.onchange('food_order_line_ids', 'room_line_ids',
                  'service_line_ids', 'vehicle_line_ids', 'event_line_ids')
    def _onchange_room_line_ids(self):
        self._compute_amount_untaxed()
        self.invoice_button_visible = False

    # ═══════════════════════════ CONSTRAINTS ═══════════════════════════════

    @api.constrains("room_line_ids")
    def _check_duplicate_folio_room_line(self):
        """Ensure the same room is not booked twice in one folio."""
        for record in self:
            seen_ids = set()
            for line in record.room_line_ids:
                if line.room_id.id in seen_ids:
                    raise ValidationError(_(
                        "Duplicate room detected: '%(room)s' appears more than once in this folio.",
                        room=line.room_id.name,
                    ))
                seen_ids.add(line.room_id.id)

    # ═══════════════════════════ ACTIONS ═══════════════════════════════════

    def action_reserve(self):
        """Reserve all rooms in this folio."""
        for rec in self:
            if rec.state == 'reserved':
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {'type': 'warning', 'message': _("Room already reserved.")},
                }
            if not rec.room_line_ids:
                raise ValidationError(_("Please add at least one room before reserving."))
            rec.room_line_ids.room_id.write({'status': 'reserved', 'is_room_avail': False})
            rec.write({'state': 'reserved'})
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'success',
                    'message': _("Rooms reserved successfully!"),
                    'next': {'type': 'ir.actions.act_window_close'},
                },
            }

    def action_cancel(self):
        """Cancel booking and release rooms."""
        for rec in self:
            rec.room_line_ids.room_id.write({'status': 'available', 'is_room_avail': True})
            rec.write({'state': 'cancel'})

    def action_checkin(self):
        """Check in all rooms in this folio."""
        for rec in self:
            if not rec.room_line_ids:
                raise ValidationError(_("Please add room details before checking in."))
            rec.room_line_ids.room_id.write({'status': 'occupied', 'is_room_avail': False})
            rec.write({'state': 'check_in', 'is_checkin': True})
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'success',
                    'message': _("Checked in successfully!"),
                    'next': {'type': 'ir.actions.act_window_close'},
                },
            }

    def action_checkout(self):
        """Check out all rooms."""
        for rec in self:
            rec.write({'state': 'check_out', 'is_checkin': False})
            for line in rec.room_line_ids:
                line.room_id.write({'status': 'available', 'is_room_avail': True})
                line.write({'checkout_date': datetime.today()})

    def action_done(self):
        """Mark booking as done after payment confirmation."""
        for rec in self:
            invoices = self.env['account.move'].search([('ref', '=', rec.name)])
            for inv in invoices:
                if inv.payment_state == 'not_paid':
                    raise ValidationError(_("Invoice is still due for payment."))
            rec.write({'state': 'done', 'is_checkin': False})

    def action_maintenance_request(self):
        """Send a maintenance request for all rooms in this folio."""
        for rec in self:
            room_ids = rec.room_line_ids.room_id.ids
            if not room_ids:
                raise ValidationError(_("Please add room details before sending a maintenance request."))
            rooms = self.env['product.template'].browse(room_ids)
            self.env['maintenance.request'].sudo().create({
                'date': fields.Date.today(),
                'state': 'draft',
                'type': 'room',
                'room_maintenance_ids': [(6, 0, rooms.ids)],
            })
            rec.maintenance_request_sent = True
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'success',
                    'message': _("Maintenance request sent successfully."),
                    'next': {'type': 'ir.actions.act_window_close'},
                },
            }

    def action_invoice(self):
        """Create invoice from all unbilled booking lines."""
        if not self.room_line_ids:
            raise ValidationError(_("Please add room details before creating an invoice."))
        booking_list = self._compute_amount_untaxed(True)
        if not booking_list:
            raise ValidationError(_("No new items to invoice."))
        account_move = self.env["account.move"].create([{
            'move_type': 'out_invoice',
            'invoice_date': fields.Date.today(),
            'partner_id': self.partner_id.id,
            'ref': self.name,
            'hotel_booking_id': self.id,
        }])
        invoice_lines = []
        for rec in booking_list:
            invoice_lines.append({
                'name': rec['name'],
                'quantity': rec['quantity'],
                'price_unit': rec['price_unit'],
                'move_id': account_move.id,
                'product_type': rec['product_type'],
            })
        self.env['account.move.line'].create(invoice_lines)
        self.write({'invoice_status': 'invoiced', 'invoice_button_visible': True})
        return {
            'type': 'ir.actions.act_window',
            'name': _('Invoice'),
            'view_mode': 'form',
            'res_model': 'account.move',
            'view_id': self.env.ref('account.view_move_form').id,
            'res_id': account_move.id,
            'context': "{'create': False}",
        }

    def action_view_invoices(self):
        """Open list of invoices for this folio."""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Invoices'),
            'view_mode': 'list,form',
            'res_model': 'account.move',
            'domain': [('ref', '=', self.name)],
            'context': "{'create': False}",
        }

    # ═══════════════════════════ DASHBOARD ═════════════════════════════════

    def get_details(self):
        """Return dashboard statistics dict for the OWL dashboard component."""
        tz_name = self.env.user.tz or 'UTC'
        today_local = datetime.now(pytz.timezone(tz_name)).date()

        total_room = self.env['product.template'].search_count([('is_room', '=', True)])
        available_room = self.env['product.template'].search_count(
            [('is_room', '=', True), ('status', '=', 'available')])
        check_in = self.env['room.booking'].search_count([('state', '=', 'check_in')])
        reservation = self.env['room.booking'].search_count([('state', '=', 'reserved')])

        # Today's check-outs
        check_out = sum(
            1 for booking in self.env['room.booking'].search([])
            for line in booking.room_line_ids
            if line.checkout_date and line.checkout_date.date() == today_local
        )

        # Staff count
        group_refs = [
            'hotel_management_odoo.hotel_group_admin',
            'hotel_management_odoo.cleaning_team_group_head',
            'hotel_management_odoo.cleaning_team_group_user',
            'hotel_management_odoo.hotel_group_reception',
            'hotel_management_odoo.maintenance_team_group_leader',
            'hotel_management_odoo.maintenance_team_group_user',
        ]
        group_ids = [self.env.ref(r).id for r in group_refs]
        staff = self.env['res.users'].search_count([('groups_id', 'in', group_ids)])

        total_vehicle = self.env['fleet.vehicle.model'].search_count([])
        booked_vehicle = self.env['fleet.booking.line'].search_count([('state', '=', 'check_in')])
        available_vehicle = total_vehicle - booked_vehicle

        events = self.env['event.event'].search([])
        total_event = len(events)
        now = fields.Datetime.now()
        today = fields.Date.today()
        pending_events = sum(1 for e in events if e.date_end >= now)
        today_events = sum(1 for e in events if e.date_end.date() == today)

        food_items = self.env['lunch.product'].search_count([])
        food_order = len(self.env['food.booking.line'].search([]).filtered(
            lambda r: r.booking_id.state not in ['check_out', 'cancel', 'done']
        ))

        total_revenue = today_revenue = pending_payment = 0.0
        for move in self.env['account.move'].search([]):
            if move.ref and 'BOOKING' in move.ref:
                if move.payment_state == 'paid':
                    total_revenue += move.amount_total
                    if move.date == today:
                        today_revenue += move.amount_total
                elif move.payment_state == 'not_paid':
                    pending_payment += move.amount_total

        currency = self.env.user.company_id.currency_id
        return {
            'total_room': total_room,
            'available_room': available_room,
            'staff': staff,
            'check_in': check_in,
            'reservation': reservation,
            'check_out': check_out,
            'total_vehicle': total_vehicle,
            'available_vehicle': available_vehicle,
            'total_event': total_event,
            'today_events': today_events,
            'pending_events': pending_events,
            'food_items': food_items,
            'food_order': food_order,
            'total_revenue': round(total_revenue, 2),
            'today_revenue': round(today_revenue, 2),
            'pending_payment': round(pending_payment, 2),
            'currency_symbol': currency.symbol,
            'currency_position': currency.position,
        }
