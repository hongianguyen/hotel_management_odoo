# -*- coding: utf-8 -*-
# ResortPro 19 - Migrated from Cybrosys Hotel Management v18
from odoo import api, fields, models


class EventBookingLine(models.Model):
    """Model that handles event bookings within a hotel folio."""
    _name = "event.booking.line"
    _description = "Hotel Event Booking Line"
    _rec_name = 'event_id'

    booking_id = fields.Many2one(
        comodel_name="room.booking",
        string="Booking",
        ondelete="cascade",
        help="Parent hotel booking reference",
    )
    event_id = fields.Many2one(
        comodel_name='event.event',
        string="Event",
        help="Event to book",
    )
    ticket_id = fields.Many2one(
        comodel_name='product.product',
        string="Ticket",
        domain=[('service_tracking', '=', 'event')],
        help="Event ticket type",
    )
    description = fields.Char(
        string='Description',
        related='event_id.display_name',
        help="Event description",
    )
    uom_qty = fields.Float(string="Quantity", default=1, help="Number of tickets")
    uom_id = fields.Many2one(
        comodel_name='uom.uom',
        readonly=True,
        string="Unit of Measure",
        related='ticket_id.uom_id',
        help="Unit of measure from the ticket product",
    )
    price_unit = fields.Float(
        related='ticket_id.lst_price',
        string='Price',
        digits='Product Price',
        help="Selling price of the selected ticket",
    )
    tax_ids = fields.Many2many(
        comodel_name='account.tax',
        relation='hotel_event_order_line_taxes_rel',
        column1='event_id',
        column2='tax_id',
        related='ticket_id.taxes_id',
        string='Taxes',
        domain=[('type_tax_use', '=', 'sale')],
        help="Taxes applied when selling event tickets",
    )
    currency_id = fields.Many2one(
        related='booking_id.pricelist_id.currency_id',
        string='Currency',
        store=True,
        precompute=True,
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
        help="Total tax amount",
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
        return self.env['account.tax']._prepare_base_line_for_taxes_computation(
            self,
            tax_ids=self.tax_ids,
            quantity=self.uom_qty,
            partner_id=self.booking_id.partner_id,
            currency_id=self.currency_id,
        )
