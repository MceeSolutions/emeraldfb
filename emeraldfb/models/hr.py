from odoo import models, fields, api


class Employee(models.Model):
    _inherit = 'hr.employee'
    
    address_home= fields.Char(string='Private Address')
    next_of_kin = fields.Char(string='Next of Kin')
    nok_address = fields.Char(string='Address')
    nok_phone = fields.Char(string='Phone Number')

    highest_level_of_education = fields.Char(string='Highest Level of Education')

    guarantor1_name = fields.Char(string='Guarantor')
    guarantor1_address = fields.Char(string='Address')
    guarantor1_phone = fields.Char(string='Phone Number')

    guarantor2_name = fields.Char(string='Guarantor')
    guarantor2_address = fields.Char(string='Address')
    guarantor2_phone = fields.Char(string='Phone Number')
    
    work_identification_number = fields.Char(string='Work Identification Number')
    
    state_id = fields.Many2one(comodel_name='res.country.state', string='State')
    local_government_area = fields.Char(string='Local Government Area')
    
    @api.multi
    def send_birthday_reminder_mail(self):

        employees = self.env['hr.employee'].search([])
        
        current_dates = False
        
        for self in employees:
            if self.birthday:
                
                current_dates = datetime.datetime.strptime(self.birthday, "%Y-%m-%d")
                current_datesz = current_dates - relativedelta(days=3)
                print(current_datesz)
                
                date_start_day = current_datesz.day
                date_start_month = current_datesz.month
                date_start_year = current_datesz.year
                
                today = datetime.datetime.now().strftime("%Y-%m-%d")
                
                test_today = datetime.datetime.today().strptime(today, "%Y-%m-%d")
                date_start_day_today = test_today.day
                date_start_month_today = test_today.month
                date_start_year_today = test_today.year
                
                
                if date_start_month == date_start_month_today:
                    if date_start_day == date_start_day_today:
                        config = self.env['mail.template'].sudo().search([('name','=','Birthday Reminder HR')], limit=1)
                        mail_obj = self.env['mail.mail']
                        if config:
                            values = config.generate_email(self.id)
                            mail = mail_obj.create(values)
                            if mail:
                                mail.send()
                            return True
        return

 
class Contract(models.Model):
    _inherit = 'hr.contract'
    
    address_home_id = fields.Many2one(
        'res.partner', 'Private Address', help='Enter here the private address of the employee, not the one linked to your company.',
        groups="hr.group_hr_user")
    
    bank_account_id = fields.Many2one(
        'res.partner.bank', 'Bank Account Number',
        groups="hr.group_hr_user",
        related="employee_id.bank_account_id",
        help='Employee bank salary account')
    
    overtime = fields.Float(string='Overtime', required=False, help="Employee's Overtime")
    deductions = fields.Float(string='Deductions', required=False, help="Employee's Deductions")


class HrExpense(models.Model):
    
    _name = "hr.expense"
    _inherit = 'hr.expense'
    
    vendor_id = fields.Many2one('res.partner', string="Vendor", domain=[('supplier', '=', True)], readonly=True, states={'draft': [('readonly', False)], 'refused': [('readonly', False)]})
    
    account_id = fields.Many2one('account.account', string='Account', states={'post': [('readonly', True)], 'done': [('readonly', True)], 'approve': [('readonly', False)]}, default=lambda self: self.env['ir.property'].get('property_account_expense_categ_id', 'product.category'),
        help="An expense account is expected")
    
    discount = fields.Float(string='Discount')
    
    @api.depends('quantity', 'unit_amount', 'discount', 'tax_ids', 'currency_id')
    def _compute_amount(self):
        for expense in self:
            expense.untaxed_amount = expense.unit_amount * expense.quantity - expense.discount
            taxes = expense.tax_ids.compute_all(expense.unit_amount, expense.currency_id, expense.quantity, expense.product_id, expense.employee_id.user_id.partner_id)
            expense.total_amount = taxes.get('total_included') - expense.discount
    
    @api.multi
    def approve_employee_expense_sheets_notification(self):
        group_id = self.env['ir.model.data'].xmlid_to_object('emeraldfb.group_coo')
        user_ids = []
        partner_ids = []
        for user in group_id.users:
            user_ids.append(user.id)
            partner_ids.append(user.partner_id.id)
        self.message_subscribe_users(user_ids=user_ids)
        subject = "Expense {} needs a COO Approval".format(self.name)
        self.message_post(subject=subject,body=subject,partner_ids=partner_ids)
        return False
    
    @api.multi
    def submit_expenses(self):
        if any(expense.state != 'draft' for expense in self):
            raise UserError(_("You cannot report twice the same line!"))
        if len(self.mapped('employee_id')) != 1:
            raise UserError(_("You cannot report expenses for different employees in the same report!"))
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'hr.expense.sheet',
            'target': 'current',
            'context': {
                'default_expense_line_ids': [line.id for line in self],
                'default_employee_id': self[0].employee_id.id,
                'default_name': self[0].name if len(self.ids) == 1 else '',
                'default_vendor_id' :  self[0].vendor_id.id if self[0].vendor_id else ''
            }
        }        
            
    
class HrExpenseSheet(models.Model):
    _name = "hr.expense.sheet"
    _inherit = 'hr.expense.sheet'
    
    expense_line_ids = fields.One2many('hr.expense', 'sheet_id', string='Expense Lines', states={'approve': [('readonly', False)], 'done': [('readonly', True)], 'post': [('readonly', True)]}, copy=False)
    state = fields.Selection([('submit', 'Submitted'),
                              ('confirm', 'Confirmed'),
                              ('approve', 'Approved'),
                              ('post', 'Posted'),
                              ('done', 'Paid'),
                              ('cancel', 'Refused')
                              ], string='Status', index=True, readonly=True, track_visibility='onchange', copy=False, default='submit', required=True,
    help='Expense Report State')
    
    @api.multi
    def approve_employee_expense_sheets(self):
        self.write({'state': 'confirm'})
        group_id = self.env['ir.model.data'].xmlid_to_object('emeraldfb.group_coo')
        user_ids = []
        partner_ids = []
        for user in group_id.users:
            user_ids.append(user.id)
            partner_ids.append(user.partner_id.id)
        self.message_subscribe_users(user_ids=user_ids)
        subject = "Expense {} needs COO Approval".format(self.name)
        self.message_post(subject=subject,body=subject,partner_ids=partner_ids)
        return False
    
    @api.multi
    def refuse_employee_expense_sheets(self):
        self.write({'state': 'cancel'})
    
    @api.multi
    def approve_expense_sheets(self):
        if not self.user_has_groups('hr.group_hr_manager'):
            raise UserError(_("Only HR Managers can approve expenses"))
        
        self.write({'state': 'approve', 'responsible_id': self.env.user.id})


# class HrSalaryRule(models.Model):
#     _inherit = 'hr.salary.rule'
#     _order = 'arrangement_sequence asc'
    
#     arrangement_sequence = fields.Integer(required=False, index=True, default=5,
#         help='Use to arrange sequence')


# class HrPayslip(models.Model):
#     _name = 'hr.payslip'
#     _inherit = 'hr.payslip'
    
#     overtime = fields.Float(string='Overtime', required=False, help="Employee's Overtime")
#     deductions = fields.Float(string='Deductions', required=False, help="Employee's Deductions")
    
# class HrPayslipWorkedDays(models.Model):
#     _inherit = 'hr.payslip.worked_days'
    
#     number_of_days = fields.Float(string='Absent Days')


# class Holidays(models.Model):
#     _name = "hr.holidays"
#     _inherit = 'hr.holidays'
    
#     date_from = fields.Date('Start Date', readonly=True, index=True, copy=False,
#         states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]}, track_visibility='onchange')
#     date_to = fields.Date('End Date', readonly=True, copy=False,
#         states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]}, track_visibility='onchange')
    
#     @api.multi
#     def send_hr_approved_mail(self):
#         config = self.env['mail.template'].sudo().search([('name','=','Leave HR Approval')], limit=1)
#         mail_obj = self.env['mail.mail']
#         if config:
#             values = config.generate_email(self.id)
#             mail = mail_obj.create(values)
#             if mail:
#                 mail.send()
                
                
#     @api.multi
#     def action_validate(self):
#         self._check_security_action_validate()

#         current_employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
#         for holiday in self:
#             if holiday.state not in ['confirm', 'validate1']:
#                 raise UserError(_('Leave request must be confirmed in order to approve it.'))
#             if holiday.state == 'validate1' and not holiday.env.user.has_group('hr_holidays.group_hr_holidays_manager'):
#                 raise UserError(_('Only an HR Manager can apply the second approval on leave requests.'))

#             holiday.write({'state': 'validate'})
#             holiday.send_hr_approved_mail()
#             if holiday.double_validation:
#                 holiday.write({'second_approver_id': current_employee.id})
#             else:
#                 holiday.write({'first_approver_id': current_employee.id})
#             if holiday.holiday_type == 'employee' and holiday.type == 'remove':
#                 holiday._validate_leave_request()
#             elif holiday.holiday_type == 'category':
#                 leaves = self.env['hr.holidays']
#                 for employee in holiday.category_id.employee_ids:
#                     values = holiday._prepare_create_by_category(employee)
#                     leaves += self.with_context(mail_notify_force_send=False).create(values)
#                 # TODO is it necessary to interleave the calls?
#                 leaves.action_approve()
#                 if leaves and leaves[0].double_validation:
#                     leaves.action_validate()
#         return True
    