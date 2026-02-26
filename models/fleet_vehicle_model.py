# -*- coding: utf-8 -*-
# ResortPro 19 - Migrated from Cybrosys Hotel Management v18
# NOTE: @tools.ormcache() on instance methods is removed - use direct env.ref
from odoo import fields, models


class FleetVehicleModel(models.Model):
    """Inherits Fleet Vehicle Model to support hotel vehicle bookings."""
    _inherit = 'fleet.vehicle.model'

    price_per_km = fields.Float(
        string="Price/KM",
        default=1.0,
        help="Rental price per kilometre",
    )
    uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string='Unit of Measure',
        help="Unit of measure (km)",
        required=True,
        default=lambda self: self.env.ref('uom.product_uom_km', raise_if_not_found=False),
    )
