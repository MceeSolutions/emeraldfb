from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = "sale.order"
    
    @api.multi
    def _default_employee(self):
         return self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
    
    sale_employee_id = fields.Many2one(comodel_name='hr.employee', string='Employee', default=_default_employee, help="Default Employee")
    
    state_id = fields.Many2one(comodel_name="res.country.state", string='State', ondelete='restrict', readonly=True, index=True, store=True)
    city = fields.Char(string='City', readonly=True, index=True, store=True)


class SaleOrderLine(models.Model):
    _name = 'sale.order.line'
    _description = 'Sales Order Line'
    _inherit = ['sale.order.line']
    
    type = fields.Selection([('sale', 'Sale'), ('transport_rebate', 'Transport Rebate'), ('monthly_rebate', 'Monthly Rebate'), ('pr', 'PR')], string='Type', required=True, default='sale', store=True)            
    
    
    @api.multi
    @api.onchange('type')
    def type_change(self):
        if self.type == 'sale':
            self.discount = 0
        else:
            self.discount = 100            
    
    
class SaleReport(models.Model):
    _name = "sale.report"
    _inherit = "sale.report"
    
    state_id = fields.Many2one(comodel_name="res.country.state", string='State', readonly=True)
    city = fields.Char(string='City', readonly=True)
    type = fields.Selection([('sale', 'Sale'), ('transport_rebate', 'Transport Rebate'), ('monthly_rebate', 'Monthly Rebate'), ('pr', 'PR')], string='Type', readonly=True)            
    
    def _select(self):
        select_str = """
            WITH currency_rate as (%s)
             SELECT min(l.id) as id,
                    l.product_id as product_id,
                    l.type as type,
                    t.uom_id as product_uom,
                    sum(l.product_uom_qty / u.factor * u2.factor) as product_uom_qty,
                    sum(l.qty_delivered / u.factor * u2.factor) as qty_delivered,
                    sum(l.qty_invoiced / u.factor * u2.factor) as qty_invoiced,
                    sum(l.qty_to_invoice / u.factor * u2.factor) as qty_to_invoice,
                    sum(l.price_total / COALESCE(cr.rate, 1.0)) as price_total,
                    sum(l.price_subtotal / COALESCE(cr.rate, 1.0)) as price_subtotal,
                    sum(l.amt_to_invoice / COALESCE(cr.rate, 1.0)) as amt_to_invoice,
                    sum(l.amt_invoiced / COALESCE(cr.rate, 1.0)) as amt_invoiced,
                    count(*) as nbr,
                    s.name as name,
                    s.date_order as date,
                    s.confirmation_date as confirmation_date,
                    s.state as state,
                    s.partner_id as partner_id,
                    s.user_id as user_id,
                    s.company_id as company_id,
                    extract(epoch from avg(date_trunc('day',s.date_order)-date_trunc('day',s.create_date)))/(24*60*60)::decimal(16,2) as delay,
                    t.categ_id as categ_id,
                    s.pricelist_id as pricelist_id,
                    s.analytic_account_id as analytic_account_id,
                    s.team_id as team_id,
                    p.product_tmpl_id,
                    partner.city as city,
                    partner.state_id as state_id,
                    partner.country_id as country_id,
                    partner.commercial_partner_id as commercial_partner_id,
                    sum(p.weight * l.product_uom_qty / u.factor * u2.factor) as weight,
                    sum(p.volume * l.product_uom_qty / u.factor * u2.factor) as volume
        """ % self.env['res.currency']._select_companies_rates()
        return select_str
    
    def _group_by(self):
        group_by_str = """
            GROUP BY l.product_id,
                    l.order_id,
                    l.type,
                    t.uom_id,
                    t.categ_id,
                    s.name,
                    s.date_order,
                    s.confirmation_date,
                    s.partner_id,
                    s.user_id,
                    s.state,
                    s.company_id,
                    s.pricelist_id,
                    s.analytic_account_id,
                    s.team_id,
                    p.product_tmpl_id,
                    partner.city,
                    partner.state_id,
                    partner.country_id,
                    partner.commercial_partner_id
        """
        return group_by_str
    