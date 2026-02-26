# -*- coding: utf-8 -*-
# ResortPro 19 - Migrated from Cybrosys Hotel Management v18
from odoo import api, fields, models


class FleetBookingLine(models.Model):
    """Model that handles vehicle bookings within a hotel folio."""
    _name = "fleet.booking.line"
    _description = "Hotel Fleet Booking Line"
    _rec_name = 'fleet_id'

    booking_id = fields.Many2one(
        comodel_name="room.booking",
        string="Booking",
        ondelete="cascade",
        help="Parent hotel booking reference",
    )
    fleet_id = fields.Many2one(
        comodel_name='fleet.vehicle.model',
        string="Vehicle",
        help="Vehicle to book",
    )
    description = fields.Char(
        string='Description',
        related='fleet_id.display_name',
        help="Vehicle description",
    )
    uom_qty = fields.Float(string="Total KM", default=1, help="Total kilometres")
    uom_id = fields.Many2one(
        comodel_name='uom.uom',
        readonly=True,
        string="Unit of Measure",
        default=lambda self: self.env.ref('uom.product_uom_km', raise_if_not_found=False),
        help="Unit of measure (km)",
    )
    price_unit = fields.Float(
        related='fleet_id.price_per_km',
        string='Rent/KM',
        digits='Product Price',
        help="Rental price per kilometre",
    )
    tax_ids = fields.Many2many(
        comodel_name='account.tax',
        relation='hotel_fleet_order_line_taxes_rel',
        column1='fleet_id',
        column2='tax_id',
        string='Taxes',
        domain=[('type_tax_use', '=', 'sale')],
        help="Taxes applied for vehicle rental",
    )
    currency_id = fields.Many2one(
        related='booking_id.pricelist_id.currency_id',
        string="Currency",
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

    def search_available_vehicle(self):
        """Return IDs of vehicles currently booked (for dashboard)."""
        return self.env['fleet.vehicle.model'].search(
            [('id', 'in', self.search([]).mapped('fleet_id').ids)]
        ).ids
