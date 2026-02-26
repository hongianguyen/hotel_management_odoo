# -*- coding: utf-8 -*-
# ResortPro 19 - Migrated from Cybrosys Hotel Management v18
from odoo import fields, models


class AccountMoveLine(models.Model):
    """Adding Product Type field to Account Move Line model."""
    _inherit = "account.move.line"

    product_type = fields.Selection(
        selection=[
            ('room', 'Room'),
            ('food', 'Food'),
            ('event', 'Event'),
            ('service', 'Service'),
            ('fleet', 'Fleet'),
        ],
        string="Product Type",
        help="Type of hotel product/service on this invoice line",
    )
