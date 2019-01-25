# -*-coding:utf-8-*-
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
    
    
class Holidays(models.Model):
    _name = "hr.holidays"
    _inherit = 'hr.holidays'
    
    
    @api.multi
    def send_hr_approved_mail(self):
        config = self.env['mail.template'].sudo().search([('name','=','Leave HR Approval')], limit=1)
        mail_obj = self.env['mail.mail']
        if config:
            values = config.generate_email(self.id)
            mail = mail_obj.create(values)
            if mail:
                mail.send()
                
                
    @api.multi
    def action_validate(self):
        self._check_security_action_validate()

        current_employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        for holiday in self:
            if holiday.state not in ['confirm', 'validate1']:
                raise UserError(_('Leave request must be confirmed in order to approve it.'))
            if holiday.state == 'validate1' and not holiday.env.user.has_group('hr_holidays.group_hr_holidays_manager'):
                raise UserError(_('Only an HR Manager can apply the second approval on leave requests.'))

            holiday.write({'state': 'validate'})
            holiday.send_hr_approved_mail()
            if holiday.double_validation:
                holiday.write({'second_approver_id': current_employee.id})
            else:
                holiday.write({'first_approver_id': current_employee.id})
            if holiday.holiday_type == 'employee' and holiday.type == 'remove':
                holiday._validate_leave_request()
            elif holiday.holiday_type == 'category':
                leaves = self.env['hr.holidays']
                for employee in holiday.category_id.employee_ids:
                    values = holiday._prepare_create_by_category(employee)
                    leaves += self.with_context(mail_notify_force_send=False).create(values)
                # TODO is it necessary to interleave the calls?
                leaves.action_approve()
                if leaves and leaves[0].double_validation:
                    leaves.action_validate()
        return True
    
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
    
    
    
class CustomerRequest(models.Model):
    
    _name = "customer.request"
    _description = "customer request form"
    _order = "name"
    _inherit = ['res.partner']
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submitted'),
        ('approve', 'Approved'),
        ('reject', 'Rejected'),
        ], string='Status', readonly=True, index=True, copy=False, default='draft', track_visibility='onchange')          
    
    @api.depends('is_company', 'parent_id.commercial_partner_id')
    def _compute_commercial_partner(self):
        return {}
         
    @api.multi
    def button_reset(self):
        self.write({'state': 'draft'})
        return {}
    
    @api.multi
    def button_submit(self):
        self.write({'state': 'submit'})
        return {}
    
    @api.multi
    def button_approve(self):
        self.write({'state': 'approve'})
        vals = {
            'name' : self.name,
            'company_type' : self.company_type,
            'image' : self.image,
            'parent_id' : self.parent_id.id,
            'street' : self.street,
            'street2' : self.street2,
            'city' : self.city,
            'state_id' : self.state_id.id,
            'zip' : self.zip,
            'country_id' : self.country_id.id,            
            'vat' : self.vat,
            'function' : self.function,
            'phone' : self.phone,
            'mobile' : self.mobile,
            'email' : self.email,
            'customer': self.customer,
            'user_id': self.user_id.id,
            'property_product_pricelist': self.property_product_pricelist.id,
            'supplier' : self.supplier,
            'supplier' : self.company_id.id
        }
        self.env['res.partner'].sudo().create(vals)
        return {}
    
    @api.multi
    def button_reject(self):
        self.write({'state': 'reject'})
        return {}
    
'''
class EmeraldProduction(models.Model):
    
    _name = "emerald.production"
    
    def _get_default_scrap_location_id(self):
        return self.env['stock.location'].search([('scrap_location', '=', True), ('company_id', 'in', [self.env.user.company_id.id, False])], limit=1).id

    def _get_default_location_id(self):
        company_user = self.env.user.company_id
        warehouse = self.env['stock.warehouse'].search([('company_id', '=', company_user.id)], limit=1)
        if warehouse:
            return warehouse.lot_stock_id.id
        return None

    name = fields.Char(
        'Reference',  default=lambda self: _('New'),
        copy=False, readonly=True, required=True,
        states={'done': [('readonly', True)]})
    origin = fields.Char(string='Source Document')
    product_id = fields.Many2one(
        'product.product', 'Product',
        required=True, states={'done': [('readonly', True)]})
    product_uom_id = fields.Many2one(
        'product.uom', 'Unit of Measure',
        required=True, states={'done': [('readonly', True)]})
    tracking = fields.Selection('Product Tracking', readonly=True, related="product_id.tracking")
    lot_id = fields.Many2one(
        'stock.production.lot', 'Lot',
        states={'done': [('readonly', True)]}, domain="[('product_id', '=', product_id)]")
    package_id = fields.Many2one(
        'stock.quant.package', 'Package',
        states={'done': [('readonly', True)]})
    owner_id = fields.Many2one('res.partner', 'Owner', states={'done': [('readonly', True)]})
    move_id = fields.Many2one('stock.move', 'Scrap Move', readonly=True)
    picking_id = fields.Many2one('stock.picking', 'Picking', states={'done': [('readonly', True)]})
    location_id = fields.Many2one(
        'stock.location', 'Location', domain="[('usage', '=', 'internal')]",
        required=True, states={'done': [('readonly', True)]}, default=_get_default_location_id)
    scrap_location_id = fields.Many2one(
        'stock.location', 'Scrap Location', default=_get_default_scrap_location_id,
        domain="[('scrap_location', '=', True)]", required=True, states={'done': [('readonly', True)]})
    scrap_qty = fields.Float('Quantity', default=1.0, required=True, states={'done': [('readonly', True)]})
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done')], string='Status', default="draft")
    date_expected = fields.Datetime('Expected Date', default=fields.Datetime.now)
    
    @api.model
    def create(self, vals):
        if 'name' not in vals or vals['name'] == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('stock.scrap') or _('New')
        scrap = super(StockScrap, self).create(vals)
        return scrap

    def unlink(self):
        if 'done' in self.mapped('state'):
            raise UserError(_('You cannot delete a scrap which is done.'))
        return super(StockScrap, self).unlink()
    
'''
    
    