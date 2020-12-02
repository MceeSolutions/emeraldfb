from odoo import models, fields, api


class ResCompany(models.Model):

    _inherit = 'res.company'

    default_ir_expense_account = fields.Many2one('account.account', "Default IR Account")
    default_ir_journal_id = fields.Many2one('account.journal', "Default IR Journal")
