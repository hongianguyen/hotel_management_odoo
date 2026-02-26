# -*- coding: utf-8 -*-
# ResortPro 19 - Migrated from Cybrosys Hotel Management v18
from odoo import fields, models


class HotelService(models.Model):
    """Model that holds all hotel services."""
    _name = 'hotel.service'
    _description = "Hotel Service"
    _inherit = 'mail.thread'
    _order = 'id desc'

    name = fields.Char(string="Service", help="Name of the service", required=True)
    unit_price = fields.Float(string="Price", help="Price of the service", default=0.0)
    taxes_ids = fields.Many2many(
        comodel_name='account.tax',
        relation='hotel_service_taxes_rel',
        column1='service_id',
        column2='tax_id',
        string='Customer Taxes',
        domain=[('type_tax_use', '=', 'sale')],
        default=lambda self: self.env.company.account_sale_tax_id,
        help="Default taxes applied when selling this service.",
    )
