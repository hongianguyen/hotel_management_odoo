# -*- coding: utf-8 -*-
# ResortPro 19 - Migrated from Cybrosys Hotel Management v18
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class RoomBookingLine(models.Model):
    """Model that handles individual room lines within a hotel folio."""
    _name = "room.booking.line"
    _description = "Hotel Folio Room Line"
    _rec_name = 'room_id'

    booking_id = fields.Many2one(
        comodel_name="room.booking",
        string="Booking",
        ondelete="cascade",
        help="Parent hotel booking",
    )
    checkin_date = fields.Datetime(
        string="Check In",
        required=True,
        help="Room check-in date and time",
    )
    checkout_date = fields.Datetime(
        string="Check Out",
        required=True,
        help="Room check-out date and time",
    )
    room_id = fields.Many2one(
        comodel_name='product.template',
        string="Room",
        domain=[('is_room', '=', True)],
        required=True,
        help="Room to book",
    )
    uom_qty = fields.Float(
        string="Duration (Days)",
        readonly=True,
        help="Number of nights computed from check-in/check-out dates",
    )
    uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string="Unit of Measure",
        readonly=True,
        default=lambda self: self.env.ref('uom.product_uom_day', raise_if_not_found=False),
        help="Unit of measure (days)",
    )
    price_unit = fields.Float(
        string="Rent/Night",
        digits='Product Price',
        compute='_compute_price_unit',
        store=True,
        help="Room price per night from pricelist",
    )
    tax_ids = fields.Many2many(
        comodel_name='account.tax',
        relation='hotel_room_order_line_taxes_rel',
        column1='room_id',
        column2='tax_id',
        related='room_id.taxes_id',
        string='Taxes',
        domain=[('type_tax_use', '=', 'sale')],
        help="Taxes applied on room rental",
    )
    currency_id = fields.Many2one(
        related='booking_id.pricelist_id.currency_id',
        string='Currency',
        help="Currency used",
    )
    price_subtotal = fields.Float(
        string="Subtotal",
        compute='_compute_price_subtotal',
        store=True,
        help="Total price excluding taxes",
    )
    price_tax = fields.Float(
        string="Tax Amount",
        compute='_compute_price_subtotal',
        store=True,
        help="Tax amount",
    )
    price_total = fields.Float(
        string="Total",
        compute='_compute_price_subtotal',
        store=True,
        help="Total price including taxes",
    )
    state = fields.Selection(
        related='booking_id.state',
        string="Order Status",
        copy=False,
        help="Status of the parent booking",
    )
    booking_line_visible = fields.Boolean(
        default=False,
        string="Invoiced",
        help="True when this line has been included in an invoice",
    )

    @api.onchange("checkin_date", "checkout_date")
    def _onchange_checkin_date(self):
        """Recompute duration when check-in or check-out changes."""
        if self.checkin_date and self.checkout_date:
            if self.checkout_date < self.checkin_date:
                raise ValidationError(_("Check-out date must be after check-in date."))
            diff = self.checkout_date - self.checkin_date
            qty = diff.days
            if diff.total_seconds() > 0:
                qty = qty + 1
            self.uom_qty = qty

    @api.onchange('checkin_date', 'checkout_date', 'room_id')
    def _onchange_room_availability(self):
        """Validate room availability for the selected dates."""
        if not (self.room_id and self.checkin_date and self.checkout_date):
            return
        records = self.env['room.booking'].search(
            [('state', 'in', ['reserved', 'check_in'])]
        )
        for rec in records:
            for line in rec.room_line_ids:
                if line.room_id == self.room_id and line.id != self._origin.id:
                    # Check date overlap
                    if (line.checkin_date <= self.checkin_date <= line.checkout_date or
                            line.checkin_date <= self.checkout_date <= line.checkout_date):
                        raise ValidationError(_(
                            "Room '%(room)s' is not available for the selected dates "
                            "due to an existing reservation.",
                            room=self.room_id.name,
                        ))

    @api.depends('room_id', 'booking_id.pricelist_id')
    def _compute_price_unit(self):
        """Compute room price from pricelist."""
        for line in self:
            price = 0.0
            if line.room_id and line.booking_id.pricelist_id:
                product = line.room_id.product_variant_id
                price = line.booking_id.pricelist_id._get_product_price(
                    product=product,
                    quantity=1.0,
                    partner=line.booking_id.partner_id,
                )
            line.price_unit = price

    @api.depends('uom_qty', 'price_unit', 'tax_ids', 'currency_id')
    def _compute_price_subtotal(self):
        """Compute subtotal/tax/total using Odoo 19 tax computation API."""
        for line in self:
            base_line = line._prepare_base_line_for_taxes_computation()
            self.env['account.tax']._add_tax_details_in_base_line(base_line, self.env.company)
            line.price_subtotal = base_line['tax_details']['raw_total_excluded_currency']
            line.price_total = base_line['tax_details']['raw_total_included_currency']
            line.price_tax = line.price_total - line.price_subtotal

    def _prepare_base_line_for_taxes_computation(self):
        """Convert record to dict for generic tax computation."""
        self.ensure_one()
        # If no pricelist, fall back to company currency
        currency = self.currency_id or self.env.company.currency_id
        return self.env['account.tax']._prepare_base_line_for_taxes_computation(
            self,
            tax_ids=self.tax_ids,
            quantity=self.uom_qty,
            partner_id=self.booking_id.partner_id,
            currency_id=currency,
        )
