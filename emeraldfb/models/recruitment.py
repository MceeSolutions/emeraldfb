from odoo import models, fields, api


class StaffRecruitment(models.Model):
    _name = "staff.recruitment"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = 'Staff Recruitment'
    
    @api.returns('self')
    def _current_employee(self):
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)],limit=1) or False
    
    @api.multi
    def send_line_manager_notification(self):
        group_id = self.env['ir.model.data'].xmlid_to_object('emerald.group_hr_line_manager')
        user_ids = []
        partner_ids = []
        for user in group_id.users:
            user_ids.append(user.id)
            partner_ids.append(user.partner_id.id)
        self.message_subscribe_users(user_ids=user_ids)
        subject = "New Staff Request Has Been Made by {}".format(self.employee_id.name)
        self.message_post(subject=subject,body=subject,partner_ids=partner_ids)
        return False
    
    @api.multi
    def send_hr_notification(self):
        group_id = self.env['ir.model.data'].xmlid_to_object('hr.group_hr_manager')
        user_ids = []
        partner_ids = []
        for user in group_id.users:
            user_ids.append(user.id)
            partner_ids.append(user.partner_id.id)
        self.message_subscribe_users(user_ids=user_ids)
        subject = "A Staff Request Has Been Made by {} and approved by Line Manager".format(self.employee_id.name)
        self.message_post(subject=subject,body=subject,partner_ids=partner_ids)
        return False
    
    state = fields.Selection(
        [('new','New'), ('submit','Submitted'), ('approve','Line Manager Approved'), ('validate','HR Approved'), ('reject','Rejected')],
        string='Status',
        default='new',
        track_visibility='onchange')
    
    #link to actual employee_id
    employee_id = fields.Many2one(
        comodel_name = 'hr.employee',
        string ='Staff Requesting',
        required = True, readonly = True,
        default = _current_employee
        )
    
    job_id = fields.Many2one(
        comodel_name = "hr.job",
        string = "Job Position",
        required = True)
    
    reason = fields.Text(
        string="Reason For Recruitment")
    
    priority = fields.Selection(
        [('0', 'nil'),
        ('50', 'Low'),
        ('100', 'Medium'), 
        ('200', 'Hign')],
        string='Priority',
        required = False,
        )
    
    @api.multi
    def button_submit(self):
        self.write({'state': 'submit'})
        return {}
    
    @api.multi
    def button_approve(self):
        self.write({'state': 'approve'})
        self.send_hr_notification()
        return {}
    
    @api.multi
    def button_approve_lm(self):
        self.write({'state': 'validate'})
        return {}
    
    @api.multi
    def button_reject(self):
        self.write({'state': 'reject'})
        return {}
