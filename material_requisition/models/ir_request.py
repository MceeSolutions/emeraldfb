# -*- coding: utf-8 -*-
from datetime import datetime
from functools import reduce
from urllib.parse import urljoin, urlencode

from odoo.exceptions import UserError, Warning

from odoo import models, fields, api, _


class IRRequest(models.Model):
    _name = 'ir.request'
    _inherit = ['mail.thread']
    _description = "Internal Requisition"
    _order = 'create_date desc, state desc, write_date desc'

    def _current_login_user(self):
        """Return current logined in user."""
        return self.env.uid

    def _current_login_employee(self):
        """Get the employee record related to the current login user."""
        hr_employee = self.env['hr.employee'].search([('user_id', '=', self._current_login_user())], limit=1)
        return hr_employee.id

    REQUEST_STAGE = [
        ('draft', 'Draft'),
        ('submit', 'Operations Manager'),
        ('approve', 'Warehouse'),
        ('transfer', 'Transfer'),
        ('done', 'Done')
    ]

    name = fields.Char(string='Number', default='/')
    state = fields.Selection(selection=REQUEST_STAGE, default='draft', track_visibility='onchange')
    requester = fields.Many2one(comodel_name='res.users', string='Requester', default=_current_login_user,
                                track_visibility='onchange')
    end_user = fields.Many2one(comodel_name='hr.employee', string='End User', default=_current_login_employee,
                               required=True)
    request_date = fields.Datetime(string='Request Date', default=lambda self: datetime.now(),
                                   help='The day in which request was initiated')
    hod = fields.Many2one(comodel_name='hr.employee', related='end_user.parent_id', string='H.O.D')
    department = fields.Many2one(comodel_name='hr.department', related='end_user.department_id', string='Department')
    dst_location_id = fields.Many2one(comodel_name='stock.location', string='Destination Location',
                                      help='Departmental Stock Location', track_visibility='onchange')
    src_location_id = fields.Many2one(comodel_name='stock.location', string='Source Location',
                                      help='Departmental Stock Location', track_visibility='onchange')
    approve_request_ids = fields.One2many(comodel_name='ir.request.approve', inverse_name='request_id',
                                          string='Request Line', required=True)
    reason = fields.Text(string='Rejection Reason')
    availaibility = fields.Boolean(string='Availaibility', compute='_compute_availabilty')
    warehouse_id = fields.Many2one(comodel_name='stock.warehouse', string='Warehouse')
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env['res.company']._company_default_get(),
                                 index=True, required=True)
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    move_id = fields.Many2one('account.move', 'Journal Entry', copy=False)
    move_name = fields.Char('Journal Name', copy=False)
    journal_id = fields.Many2one('account.journal', "Journal")
    account_id = fields.Many2one('account.account', 'Account', help='This is an expense account which will be Debited')
    can_confirm = fields.Boolean(string="Ready to confirm", compute="_compute_confirm",
                                  help="Warehouse officer can confirm")

    def _compute_confirm(self):
        self.can_confirm = bool(self.approve_request_ids) and self._confirm_lines_valid()

    def _confirm_lines_valid(self):
        return all(line.qty >= line.quantity for line in self.approve_request_ids)

    @api.multi
    def action_move_create(self):
        """ Creates requisition related financial move lines """
        account_move = self.env['account.move']

        for request in self:
            if not request.journal_id.sequence_id:
                raise UserError(_('Please define sequence on the journal related to this request.'))
            if any(request.approve_request_ids.filtered(lambda line: not line.account_id)):
                raise UserError(_("There is a line without any account. Please configure a stock account "
                                  "for all product categories that have products on the lines"))
            if not request.approve_request_ids:
                raise UserError(_('Please add at least one line!'))
            if request.move_id:
                continue

            company_currency = request.company_id.currency_id
            partner_id = request.end_user.user_id.partner_id.id
            iml = request.approve_request_line_move_line_get()
            name = request.name or ''
            credit = 0.0
            debit = reduce(lambda x, y: x + y, [line.get('credit', 0.0) for line in iml])

            iml.append({
                'name': self.name or "/",
                'account_id': request.account_id.id,
                'currency_id': company_currency.id,
                'date_maturity': fields.Date.context_today(self),
                'debit': debit,
                'credit': credit,
                'partner_id': partner_id
            })

            iml = [(0, 0, line_item) for line_item in iml]
            move_vals = {
                'ref': request.name,
                'line_ids': iml,
                'name': self.name or "/",
                'journal_id': request.journal_id.id,
                'date': fields.Date.context_today(self),
                'partner_id': partner_id,
                'narration': request.name,
            }
            move = account_move.with_context(check_move_validity=False).create(move_vals)
            move.post()
            vals = {
                'move_id': move.id,
                'move_name': move.name,
            }
            request.write(vals)
        return True

    @api.model
    def approve_request_line_move_line_get(self):
        res = []
        for line in self.approve_request_ids:
            if not line.account_id:
                continue
            if line.quantity == 0:
                continue

            credit = debit = 0.0
            credit += line.product_id.standard_price

            move_line_dict = {
                'name': line.name,
                'quantity': line.quantity,
                'account_id': line.account_id.id,
                'product_id': line.product_id.id,
                'uom_id': line.uom.id,
                'date_maturity': fields.Date.context_today(self),
                'debit': debit,
                'credit': credit
            }
            res.append(move_line_dict)
        return res

    @api.depends('approve_request_ids')
    @api.one
    def _compute_availabilty(self):
        count_total = len(self.approve_request_ids)
        count_avail = len([appr_id.state for appr_id in self.approve_request_ids if appr_id.state == 'available'])
        self.availaibility = count_total == count_avail

    @api.model
    def create(self, vals):
        default_ir_expense_account = self.sudo().env.user.company_id.default_ir_expense_account
        default_ir_journal_id = self.sudo().env.user.company_id.default_ir_journal_id
        account_vals = {
            'account_id': default_ir_expense_account.id,
            'journal_id': default_ir_journal_id.id,
        }
        vals.update(account_vals)
        res = super(IRRequest, self).create(vals)
        return res

    @api.multi
    def submit(self, context):
        seq = self.env['ir.sequence'].next_by_code('ir.request')
        recipient = self.recipient('hod', self.hod)
        url = self.request_link()
        # mail_template = self.env.ref('material_requisition.material_requisition_submit')
        # mail_template.with_context({'recipient': recipient, 'url': url}).send_mail(self.id, force_send=True)
        self.write({'state': 'submit', 'name': seq})

    @api.multi
    def department_manager_approve(self, context):
        if self:
            approved = context.get('approved')
            if not approved:
                # send rejection mail to the author.
                return {
                    "type": "ir.actions.act_window",
                    "res_model": 'ir.request.wizard',
                    "views": [[False, "form"]],
                    "context": {'request_id': self.id},
                    "target": "new",
                }
                self.write({'state': 'draft'})
            else:
                # move to next level and send mail
                url = self.request_link()
                recipient = self.recipient('department_manager', self.department)
                # mail_template = self.env.ref('material_requisition.material_requisition_approval')
                # mail_template.with_context({'recipient': recipient, 'url': url}).send_mail(self.id, force_send=True)
                self.write({'state': 'approve'})

    @api.multi
    def warehouse_officer_confirm_qty(self):
        """Forward the available quantity to warehouse officer."""
        if self.approve_request_ids is None or self.approve_request_ids is False:
            raise UserError("No line(s) defined!")
        self._compute_confirm()
        for line in self.approve_request_ids:
            line._compute_state()
        raise Warning("Please procure the items that are short in stock or process pending purchase agreements and try again!")

    @api.multi
    def proceed_after_procurement(self):
        self.state = 'approve'

    @api.multi
    def confirmation(self, context):
        approved = context.get('approved')
        if not approved:
            # send mail to the author.
            return {
                "type": "ir.actions.act_window",
                "res_model": 'ir.request.wizard',
                "views": [[False, "form"]],
                "context": {'request_id': self.id},
                "target": "new",
            }
        else:
            self.name = self.env['ir.sequence'].next_by_code("ng.ir.request")
            # move to next level and send mail
            self.write({'state': 'transfer'})

    @api.multi
    def do_transfer(self):
        if self:
            src_location_id = self.src_location_id.id
            dst_location_id = self.dst_location_id.id
            domain = [
                ('code', '=', 'internal'),
                ('warehouse_id', '=', self.warehouse_id.id),
                ('active', '=', True)
            ]
            stock_picking = self.env['stock.picking']
            picking_type = self.env['stock.picking.type'].search(domain, limit=1)
            payload = {
                'location_id': src_location_id,
                'location_dest_id': dst_location_id,
                'picking_type_id': picking_type.id
            }
            stock_picking_id = stock_picking.create(payload)
            self.stock_move(self.approve_request_ids, stock_picking_id)
            self.process(stock_picking_id)
            self.action_move_create()

    def stock_move(self, request_ids, picking_id):
        """."""
        stock_move = self.env['stock.move']
        for request_id in request_ids:
            payload = {
                'product_id': request_id.product_id.id,
                'name': request_id.product_id.name,
                'product_uom_qty': request_id.quantity,
                'product_uom': request_id.uom.id,
                'picking_id': picking_id.id,
                'location_id': picking_id.location_id.id,
                'location_dest_id': picking_id.location_dest_id.id
            }
            move = stock_move.create(payload)
            request_id.write({'transferred': True})
        self.write({'state': 'done'})

    def process(self, picking_id):
        if picking_id.state == 'draft':
            picking_id.action_confirm()
        if picking_id.state != 'assigned':
            picking_id.action_assign()
        if picking_id.state != 'assigned':
            raise UserError(_(
                "Could not reserve all requested products. Please use the \'Mark as Todo\' button to handle the reservation manually."))
        picking_id.sudo().process_move()
        immediate_transfer_wiz = self.env['stock.immediate.transfer'].search([('pick_ids', 'in', picking_id.ids)])
        immediate_transfer_wiz and immediate_transfer_wiz.process()
        # hook up journal entries in here

        url = self.request_link()
        recipient = self.recipient('department_manager', self.department)
        # mail_template = self.env.ref('material_requisition.material_requisition_transfer')
        # mail_template.with_context({'recipient': recipient, 'url': url}).send_mail(self.id, force_send=False)

    def recipient(self, recipient, model):
        """Return recipient email address."""
        if recipient == 'hod':
            workmails = model.address_id, model.work_email
            workmail = {workmail for workmail in workmails if workmail}
            workmail = workmail.pop() if workmail else model.work_email
            if not isinstance(workmail, str):
                try:
                    return workmail.email
                except:
                    pass
            return workmail
        elif recipient == 'department_manager':
            manager = model.manager_id
            return manager.work_email or manager.address_id.email

    def request_link(self):
        fragment = {}
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        model_data = self.env['ir.model.data']
        fragment.update(base_url=base_url)
        fragment.update(
            menu_id=model_data.get_object_reference('material_requisition', 'material_requisition_menu_1')[-1])
        fragment.update(model='ir.request')
        fragment.update(view_type='form')
        fragment.update(
            action=model_data.get_object_reference('material_requisition', 'material_requisition_action_window')[
                -1])
        fragment.update(id=self.id)
        query = {'db': self.env.cr.dbname}
        res = urljoin(base_url, "?%s#%s" % (urlencode(query), urlencode(fragment)))
        return res


class IRRequestApprove(models.Model):
    _name = 'ir.request.approve'

    STATE = [
        ('not_available', 'Not Available'),
        ('partially_available', 'Partially Available'),
        ('available', 'Available'),
        ('awaiting', 'Awaiting Availability'),
    ]

    request_id = fields.Many2one(comodel_name='ir.request', string='Request')
    product_id = fields.Many2one(comodel_name='product.product', string='Product')
    account_id = fields.Many2one('account.account', string="Account")
    name = fields.Char("Description")
    quantity = fields.Float(string='Quantity', default=1.0)
    uom = fields.Many2one(comodel_name='product.uom', string='U.O.M')
    qty = fields.Float(string='Qty Available', compute='_compute_qty')
    state = fields.Selection(selection=STATE, string='State', compute='_compute_state', store=False)
    transferred = fields.Boolean(string='Transferred', default=False)

    @api.model
    def create(self, vals):
        if not vals.get("account_id", False):
            product = self.env['product.product'].browse(vals.get('product_id'))
            vals['account_id'] = product.categ_id.property_stock_valuation_account_id.id
        return super(IRRequestApprove, self).create(vals)

    @api.onchange('product_id')
    def change_product(self):
        if self.product_id:
            self.uom = self.product_id.product_tmpl_id.uom_id.id
            self.name = self.product_id.product_tmpl_id.name

    @api.depends('product_id')
    @api.one
    def _compute_qty(self):
        location_id = self.request_id.src_location_id.id
        product_id = self.product_id.id
        stock_quants = self.env['stock.quant'].search(
            [('location_id', '=', location_id), ('product_id', '=', product_id)])
        self.qty = sum([stock_quant.quantity for stock_quant in stock_quants])

    @api.depends('qty')
    @api.one
    def _compute_state(self):
        if self.qty <= 0:
            self.state = 'not_available'
        elif self.qty > 0 and self.qty < self.quantity:
            self.state = 'partially_available'
        else:
            self.state = 'available'

    @api.multi
    def procure(self, context):
        product_id, quantity = self.product_id, self.quantity - self.qty
        requisition = self.env['purchase.requisition']
        line = self.env['purchase.requisition.line']
        request_identity = self.request_id.name
        requisition_id = requisition.create({'from_ir': True})
        payload = {
            'product_id': product_id.id,
            'product_uom_id': product_id.uom_id.id,
            'product_qty': quantity,
            'qty_ordered': quantity,
            'requisition_id': requisition_id.id,
            'price_unit': product_id.standard_price
        }
        line.create(payload)
        origin = '{}/{}'.format(request_identity, requisition_id.name)
        self.request_id.state = 'awaiting_procurement'
        requisition_id.write({'name': origin})
