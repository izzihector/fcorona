# -*- coding: utf-8 -*-
from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # Función que limita los envíos disponibles al cliente, si es EXCLUSIVO ya no mosgtrar más
    def _get_delivery_methods(self):
        address = self.partner_shipping_id
        # searching on website_published will also search for available website (_search method on computed field)
        carrier_ids = self.env['delivery.carrier'].sudo().search(
            [('website_published', '=', True)]).available_carriers(address)
        exclusive_found = False
        result_carrier_ids = []
        for carrier_id in carrier_ids:
            if carrier_id.is_exclusive and exclusive_found is False:
                exclusive_found = True
            elif not carrier_id.is_exclusive and exclusive_found is True:
                break
            result_carrier_ids.append(carrier_id.id)
        return self.env['delivery.carrier'].browse(result_carrier_ids)
