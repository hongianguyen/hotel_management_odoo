# -*- coding: utf-8 -*-
# ResortPro 19 - Migrated from Cybrosys Hotel Management v18
from odoo import api, fields, models


class ServiceBookingLine(models.Model):
    """Model that handles hotel service bookings within a folio."""
    _name = "service.booking.line"
    _description = "Hotel Service Booking Line"

    booking_id = fields.Many2one(
        comodel_name="room.booking",
        string="Booking",
        ondelete="cascade",
        help="Parent hotel booking reference",
    )
    service_id = fields.Many2one(
        comodel_name='hotel.service',
        string="Service",
        help="Hotel service to add",
    )
    description = fields.Char(
        string='Description',
        related='service_id.name',
        help="Service description",
    )
    uom_qty = fields.Float(string="Qty", default=1.0, help="Quantity of service units")
    uom_id = fields.Many2one(
        comodel_name='uom.uom',
        readonly=True,
        string="Unit of Measure",
        default=lambda self: self.env.ref('uom.product_uom_unit', raise_if_not_found=False),
        help="Unit of measure",
    )
    price_unit = fields.Float(
        related='service_id.unit_price',
        string='Price',
        digits='Product Price',
        help="Price of the service",
    )
    tax_ids = fields.Many2many(
        comodel_name='account.tax',
        relation='hotel_service_order_line_taxes_rel',
        column1='service_id',
        column2='tax_id',
        related='service_id.taxes_ids',
        string='Taxes',
        domain=[('type_tax_use', '=', 'sale')],
        help="Taxes applied on this service",
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

    @api.depends('uom_qty', 'price_unit', 'tax_ids')
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
