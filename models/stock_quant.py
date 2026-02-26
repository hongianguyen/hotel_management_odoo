# -*- coding: utf-8 -*-
# ResortPro 19 - Migrated from Cybrosys Hotel Management v18
from odoo import models, api, _
from odoo.exceptions import ValidationError


class StockQuant(models.Model):
    """Restrict stock quantity updates for room products."""
    _inherit = 'stock.quant'

    @api.model_create_multi
    def create(self, vals_list):
        """Block creation of stock quant for room products."""
        for vals in vals_list:
            if vals.get('product_id'):
                product = self.env['product.product'].browse(vals['product_id'])
                if product.is_room:
                    raise ValidationError(
                        _("Stock quantity cannot be updated for Room products."))
        return super().create(vals_list)

    def write(self, vals):
        """Block quantity write for room products."""
        if 'inventory_quantity' in vals or 'quantity' in vals:
            for record in self:
                if record.product_id.is_room:
                    raise ValidationError(
                        _("Stock quantity cannot be updated for Room products."))
        return super().write(vals)
