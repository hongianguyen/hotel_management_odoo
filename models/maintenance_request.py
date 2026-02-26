# -*- coding: utf-8 -*-
# ResortPro 19 - Migrated from Cybrosys Hotel Management v18
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class MaintenanceRequest(models.Model):
    """Model that handles hotel maintenance requests."""
    _name = 'maintenance.request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'sequence'
    _description = "Maintenance Request"

    sequence = fields.Char(
        readonly=True, string="Sequence", copy=False, default='New',
        help='Sequence number for identifying the maintenance request',
    )
    date = fields.Date(
        string="Date", help="Date of maintenance request",
        default=fields.Date.today,
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('team_leader_approve', 'Waiting For User Assign'),
            ('pending', 'Pending User Acceptance'),
            ('ongoing', 'Ongoing'),
            ('support', 'Waiting For Support'),
            ('done', 'Done'),
            ('verify', 'Pending Verification'),
            ('cancel', 'Cancelled'),
        ],
        default='draft', string="State",
        help="State of the maintenance request",
        tracking=True,
    )
    team_id = fields.Many2one(
        comodel_name='maintenance.team',
        string='Maintenance Team',
        help="Team assigned to this request",
        tracking=True,
    )
    team_head_id = fields.Many2one(
        comodel_name='res.users',
        related='team_id.user_id',
        string='Team Leader',
        help="Head of the maintenance team",
    )
    assigned_user_id = fields.Many2one(
        comodel_name='res.users',
        string='Assigned User',
        tracking=True,
        help="User assigned to execute this request",
    )
    type = fields.Selection(
        selection=[
            ('room', 'Room'),
            ('vehicle', 'Vehicle'),
            ('hotel', 'Hotel'),
            ('cleaning', 'Cleaning'),
        ],
        string="Type",
        help="Type of area/item requiring maintenance",
        tracking=True,
    )
    room_maintenance_ids = fields.Many2many(
        comodel_name='product.template',
        string="Room Maintenance",
        help="Rooms that need maintenance",
    )
    hotel_maintenance = fields.Char(string='Hotel Area', help="Hotel area needing maintenance")
    cleaning_maintenance = fields.Char(string='Cleaning Area', help="Area needing cleaning maintenance")
    vehicle_maintenance_id = fields.Many2one(
        comodel_name='fleet.vehicle.model',
        string="Vehicle",
        help="Vehicle requiring maintenance",
    )
    support_team_ids = fields.Many2many(
        comodel_name='res.users',
        string="Support Team",
        help="Additional support team members",
    )
    support_reason = fields.Char(string='Support Reason', help="Reason for requesting additional support")
    remarks = fields.Char(string='Remarks', help="Completion remarks")
    domain_partner_ids = fields.Many2many(
        comodel_name='res.partner',
        string="Partner Domain",
        help="Used for filtering assignable users",
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Generate sequence on create. Odoo 19: use model_create_multi."""
        for vals in vals_list:
            if vals.get('sequence', 'New') == 'New':
                vals['sequence'] = self.env['ir.sequence'].next_by_code(
                    'maintenance.request') or 'New'
        return super().create(vals_list)

    @api.onchange('team_id')
    def _onchange_team_id(self):
        """Filter assignable users based on selected team."""
        self.domain_partner_ids = self.team_id.member_ids.mapped('partner_id')

    def action_assign_team(self):
        """Move to team_leader_approve state."""
        for rec in self:
            if not rec.team_id:
                raise ValidationError(_("Please assign a Maintenance Team."))
            rec.state = 'team_leader_approve'

    def action_assign_user(self):
        """Move to pending state."""
        for rec in self:
            if not rec.assigned_user_id:
                raise ValidationError(_("Please assign a User."))
            rec.state = 'pending'

    def action_start(self):
        """Move to ongoing state."""
        self.write({'state': 'ongoing'})

    def action_support(self):
        """Move to support state (requires reason)."""
        for rec in self:
            if not rec.support_reason:
                raise ValidationError(_('Please enter the support reason.'))
            rec.state = 'support'

    def action_complete(self):
        """Move to verify state (requires remarks)."""
        for rec in self:
            if not rec.remarks:
                raise ValidationError(_('Please add a remark before completing.'))
            rec.state = 'verify'

    def action_assign_support(self):
        """Resume with support team."""
        for rec in self:
            if not rec.support_team_ids:
                raise ValidationError(_('Please choose a support team member.'))
            rec.state = 'ongoing'

    def action_verify(self):
        """Finalise: move to done and mark vehicle as available."""
        for rec in self:
            rec.state = 'done'
            if rec.vehicle_maintenance_id:
                rec.vehicle_maintenance_id.status = 'available'
