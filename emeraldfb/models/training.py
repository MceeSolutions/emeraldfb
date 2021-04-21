from odoo import models, fields, api


class TrainingTracker(models.Model):
    _name = 'emeraldfb.training.tracker'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = 'Employee Training Tracker'
    
    state = fields.Selection(
        [('new','New'), ('validate','HR Approved'), ('approve','Line Manager Approved'), ('reject','Rejected')],
        string='Status',
        default='new',
        track_visibility='onchange')
    
    #link to actual employee_id
    employee_id = fields.Many2one(
        comodel_name = 'hr.employee',
        string ='Staff',
        required=1
        )
    #pull this from employee records and set required to true
    position = fields.Char(
        related='employee_id.job_id.name',
        readonly=True,
        string='Position'
        )
    provider = fields.Many2one(
        comodel_name = 'res.partner',
        string='Provider',
        required=1
        )
    training_date_end = fields.Datetime(
        string = 'Training End Date'
        )
    #in case training lasts for days/weeks -- else, duration will be set to less than 20 hours
    training_start_date = fields.Datetime(
        string= 'Training Start Date'
        )
    unit = fields.Char(
        string='Unit',
        )
    capability = fields.Selection(
        [('0', 'Very Poor'),
        ('50', 'Poor'),
        ('100', 'Fair'), 
        ('200', 'Good'), 
        ('300', 'Very Good'), 
        ('400', 'Excellent')],
        string='Capability Level',
        required=0,
        )
    review = fields.Date(
        string ='Next Training Date'
        )
    notes = fields.Text(
        string='Notes'
        )
    
    employee = fields.Char(
        string='Employee ID', readonly=True, index=True, copy=False, default='New')
    
    @api.model
    def create(self, vals):
        if vals.get('employee', 'New') == 'New':
            vals['employee'] = self.env['ir.sequence'].next_by_code('emeraldfb.training.tracker') or '/'
        return super(TrainingTracker, self).create(vals)
    
    @api.multi
    def name_get(self):
        res = []
 
        for partner in self:
            result = partner.employee_id.name
            if partner.employee:
                result = str(partner.employee_id.name) + " " + str(partner.employee)
            res.append((partner.id, result))
        return res
    
    @api.multi
    def button_approve(self):
        self.write({'state': 'validate'})
        return {}
    
    @api.multi
    def button_approve_lm(self):
        self.write({'state': 'approve'})
        return {}
    
    @api.multi
    def button_reject(self):
        self.write({'state': 'reject'})
        return {}
    
  