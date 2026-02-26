# -*- coding: utf-8 -*-
# ResortPro 19 - Migrated from Cybrosys Hotel Management v18
from odoo import fields, models


class HotelFloor(models.Model):
    """Model that holds the Hotel Floors."""
    _name = "hotel.floor"
    _description = "Hotel Floor"
    _order = 'id desc'

    name = fields.Char(string="Name", help="Name of the floor", required=True)
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='Manager',
        help="Floor manager",
        required=True,
    )
