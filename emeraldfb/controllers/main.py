# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http, _
from odoo.addons.website_event.controllers.main import WebsiteEventController
from odoo.http import request

class Payments(http.Controller):
    
    @http.route('/shop/payment_successful', type='http', auth='public', methods=['POST'], website=True, csrf=False)
    def show_payment_successful_webpage(self, **kw):
        return http.request.render('emeraldfb.paid_thank_you', {})
        
    @http.route('/shop/payment_failed', type='http', auth='public', methods=['POST'], website=True, csrf=False)
    def show_payment_failed_webpage(self, **kw):
        return http.request.render('emeraldfb.payment_failed', {})