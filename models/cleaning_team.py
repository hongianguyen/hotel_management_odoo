# -*- coding: utf-8 -*-
# ResortPro 19 - Migrated from Cybrosys Hotel Management v18
from odoo import fields, models


class CleaningTeam(models.Model):
    """Model for creating Cleaning Teams and assigning cleaning requests."""
    _name = "cleaning.team"
    _description = "Cleaning Team"

    name = fields.Char(string="Team Name", help="Name of the cleaning team", required=True)
    team_head_id = fields.Many2one(
        comodel_name='res.users',
        string="Team Head",
        domain=lambda self: [
            ('groups_id', 'in', self.env.ref(
                'hotel_management_odoo.cleaning_team_group_head').id)
        ],
        help="Head of the cleaning team",
    )
    member_ids = fields.Many2many(
        comodel_name='res.users',
        string="Members",
        domain=lambda self: [
            ('groups_id', 'in', self.env.ref(
                'hotel_management_odoo.cleaning_team_group_user').id)
        ],
        help="Cleaning team members",
    )
