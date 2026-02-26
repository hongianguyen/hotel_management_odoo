# -*- coding: utf-8 -*-
# ResortPro 19 - Migrated from Cybrosys Hotel Management v18
# Odoo 19 Community + Python 3.12 compatible
from odoo import fields, models


class AccountMove(models.Model):
    """Inherited account.move for adding hotel booking reference field to
    invoicing model."""
    _inherit = "account.move"

    hotel_booking_id = fields.Many2one(
        comodel_name='room.booking',
        string="Booking Reference",
        readonly=True,
        help="Hotel booking reference linked to this invoice",
    )
