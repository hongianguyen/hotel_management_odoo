# -*- coding: utf-8 -*-
# ResortPro 19 - Migrated from Cybrosys Hotel Management v18
from odoo import fields, models


class HotelAmenity(models.Model):
    """Model that handles all amenities of the hotel/resort."""
    _name = 'hotel.amenity'
    _description = "Hotel Amenity"
    _inherit = 'mail.thread'
    _order = 'id desc'

    name = fields.Char(string='Name', help="Name of the amenity", required=True)
    icon = fields.Image(string="Icon", required=True, help="Image/icon of the amenity")
    description = fields.Html(string="About", help="Detailed amenity description")
