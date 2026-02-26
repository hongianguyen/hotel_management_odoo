# -*- coding: utf-8 -*-
# ResortPro 19 - Migrated from Cybrosys Hotel Management v18
from odoo import fields, models


class MaintenanceTeam(models.Model):
    """Model that handles hotel maintenance teams."""
    _name = "maintenance.team"
    _description = "Maintenance Team"

    name = fields.Char(string='Maintenance Team', help='Name of the maintenance team', required=True)
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='Team Leader',
        domain=lambda self: [
            ('groups_id', 'in', self.env.ref(
                'hotel_management_odoo.maintenance_team_group_leader').id)
        ],
        help="Leader of the maintenance team",
    )
    member_ids = fields.Many2many(
        comodel_name='res.users',
        string='Members',
        domain=lambda self: [
            ('groups_id', 'in', self.env.ref(
                'hotel_management_odoo.maintenance_team_group_user').id)
        ],
        help="Members of the maintenance team",
    )
