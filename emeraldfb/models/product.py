from odoo import models, fields
from odoo.addons import decimal_precision as dp


class Product(models.Model):
    _inherit = "product.product"

    website_price = fields.Float('Website price', store=True, readonly=False, digits=dp.get_precision('Product Price'))
    online_website_price = fields.Float('Online price', related='website_price', readonly=False)
