from odoo import models, fields, api


class PurchaseRequisition(models.Model):

	_inherit = 'purchase.requisition'

	from_ir = fields.Boolean("From IR")


class PurchaseOrder(models.Model):

	_inherit = 'purchase.order'

	from_ir = fields.Boolean("From IR")
