# -*- coding: utf-8 -*-
# ResortPro 19 - Migrated from Cybrosys Hotel Management v18
# Odoo 19: product.template field 'type' values: 'consu', 'service'
#          'is_storable' removed; storable = type='consu' + can_be_expensed etc.
#          In v19, 'consu' = consumable (no tracking), use detailed_type if needed.
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    """Extends product.template with hotel room configuration fields."""
    _inherit = "product.template"

    is_room = fields.Boolean(string="Is Room", help="Check if this product is a hotel room")
    status = fields.Selection(
        selection=[
            ("available", "Available"),
            ("reserved", "Reserved"),
            ("occupied", "Occupied"),
        ],
        default="available",
        string="Room Status",
        help="Current status of the room",
        tracking=True,
    )
    is_room_avail = fields.Boolean(
        default=True,
        string="Available",
        help="Whether the room is currently available for booking",
    )
    room_amenities_ids = fields.Many2many(
        comodel_name="hotel.amenity",
        string="Room Amenities",
        help="List of amenities available in this room",
    )
    floor_id = fields.Many2one(
        comodel_name='hotel.floor',
        string='Floor',
        help="Floor where this room is located",
        tracking=True,
    )
    user_id = fields.Many2one(
        comodel_name='res.users',
        string="Floor Manager",
        related='floor_id.user_id',
        help="Manager of the floor",
        tracking=True,
    )
    room_type = fields.Selection(
        selection=[
            ('single', 'Single'),
            ('double', 'Double'),
            ('dormitory', 'Dormitory'),
        ],
        required=True,
        string="Room Type",
        help="Type of room",
        tracking=True,
        default="single",
    )
    num_person = fields.Integer(
        string='Number Of Persons',
        required=True,
        help="Maximum capacity of the room",
        tracking=True,
        default=1,
    )

    @api.constrains("num_person")
    def _check_capacity(self):
        """Ensure room capacity is a positive number."""
        for room in self:
            if room.is_room and room.num_person <= 0:
                raise ValidationError(_("Room capacity must be greater than 0."))

    @api.onchange("room_type")
    def _onchange_room_type(self):
        """Auto-fill number of persons based on room type."""
        capacity_map = {'single': 1, 'double': 2, 'dormitory': 4}
        if self.room_type:
            self.num_person = capacity_map.get(self.room_type, 1)

    @api.onchange('is_room')
    def _onchange_is_room(self):
        """Force consumable type for room products (no stock tracking)."""
        if self.is_room:
            # Odoo 19: set type='consu' to prevent stock tracking for rooms
            self.type = 'consu'
