# -*- coding: utf-8 -*-
# ResortPro 19 - Migrated from Cybrosys Hotel Management v18
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CleaningRequest(models.Model):
    """Model for creating and assigning Cleaning Requests."""
    _name = "cleaning.request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "sequence"
    _description = "Cleaning Request"

    sequence = fields.Char(
        string="Sequence", readonly=True, default='New',
        copy=False, tracking=True,
        help="Sequence for identifying the cleaning request",
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('assign', 'Assigned'),
            ('ongoing', 'Cleaning'),
            ('support', 'Waiting For Support'),
            ('done', 'Completed'),
        ],
        string="State", default='draft',
        help="Current state of the cleaning request",
    )
    cleaning_type = fields.Selection(
        selection=[
            ('room', 'Room'),
            ('hotel', 'Hotel'),
            ('vehicle', 'Vehicle'),
        ],
        required=True, tracking=True,
        string="Cleaning Type",
        help="What area/item needs to be cleaned",
    )
    room_id = fields.Many2one(
        comodel_name='product.template',
        string="Room",
        domain=[('is_room', '=', True)],
        help="Room to be cleaned",
    )
    hotel = fields.Char(string="Hotel Area", help="Hotel area to be cleaned")
    vehicle_id = fields.Many2one(
        comodel_name='fleet.vehicle.model',
        string="Vehicle",
        help="Vehicle to be cleaned",
    )
    support_team_ids = fields.Many2many(
        comodel_name='res.users',
        string="Support Team",
        help="Support team members",
    )
    support_reason = fields.Char(string='Support Reason', help="Reason for requesting support")
    description = fields.Char(string="Description", help="Cleaning request description")
    team_id = fields.Many2one(
        comodel_name='cleaning.team',
        string="Team",
        required=True, tracking=True,
        help="Assigned cleaning team",
    )
    head_id = fields.Many2one(
        comodel_name='res.users',
        string="Head",
        related='team_id.team_head_id',
        help="Head of the cleaning team",
    )
    assigned_id = fields.Many2one(
        comodel_name='res.users',
        string="Assigned To",
        help="Team member assigned to this request",
    )
    domain_partner_ids = fields.Many2many(
        comodel_name='res.partner',
        string="Domain Partner",
        help="Used for filtering assignable users",
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Generate sequence on create. Odoo 19: use model_create_multi."""
        for vals in vals_list:
            if vals.get('sequence', 'New') == 'New':
                vals['sequence'] = self.env['ir.sequence'].next_by_code(
                    'cleaning.request') or 'New'
        return super().create(vals_list)

    @api.onchange('team_id')
    def _onchange_team_id(self):
        """Update domain_partner_ids when team changes."""
        self.domain_partner_ids = self.team_id.member_ids.mapped('partner_id')

    def action_assign_cleaning(self):
        """Set state to assigned."""
        self.write({'state': 'assign'})

    def action_start_cleaning(self):
        """Set state to ongoing."""
        self.write({'state': 'ongoing'})

    def action_done_cleaning(self):
        """Set state to done."""
        self.write({'state': 'done'})

    def action_assign_support(self):
        """Set state to support (requires reason)."""
        for rec in self:
            if not rec.support_reason:
                raise ValidationError(_('Please enter the support reason.'))
            rec.write({'state': 'support'})

    def action_assign_assign_support(self):
        """Resume cleaning with support team."""
        for rec in self:
            if not rec.support_team_ids:
                raise ValidationError(_('Please select a support team member.'))
            rec.write({'state': 'ongoing'})

    def action_maintain_request(self):
        """Create a maintenance request from cleaning request."""
        self.env['maintenance.request'].sudo().create({
            'date': fields.Date.today(),
            'state': 'draft',
            'type': self.cleaning_type,
            'vehicle_maintenance_id': self.vehicle_id.id,
        })
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'message': _("Maintenance Request created successfully."),
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }
