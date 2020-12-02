# -*- coding: utf-8 -*-
from odoo import api, fields, models

class IRRequest(models.TransientModel):
	"""docstring for IRReasons"""

	_name = 'ir.request.wizard'

	reason = fields.Text(string='Reason', required=True)

	@api.multi
	def reject(self):
		request_id = self.env.context.get('request_id')
		if request_id:
			request_id = self.env['ng.ir.request'].browse([request_id])
			# send email here
			request_id.write({'state': 'draft', 'reason':self.reason})
			return {'type': 'ir.actions.act_window_close'}
