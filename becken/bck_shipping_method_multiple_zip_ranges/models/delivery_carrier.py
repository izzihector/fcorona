# -*- coding: utf-8 -*-
from odoo import models, fields
import logging

_logger = logging.getLogger(__name__)


class DeliveryCarrierZip(models.Model):
    _name = 'delivery.carrier.zip'
    _description = 'Zip Code Range'
    _order = 'delivery_carrier_id, zip_from, zip_to'

    delivery_carrier_id = fields.Many2one(
        'delivery.carrier',
        string='Delivery Carrier',
        required=True,
        help='')
    zip_from = fields.Char('Zip From', required=True,)
    zip_to = fields.Char('Zip To', required=True,)


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    zip_ids = fields.One2many(
        comodel_name='delivery.carrier.zip', inverse_name='delivery_carrier_id', string='Zip Code Ranges')
    is_exclusive = fields.Boolean(
        string="Is Exclusive?", default=False,
        help='If a Deliverry Carrier is Exclusive, is not necessary to show the next Delivery Carries, '
        'sort by sequence.')

    def _match_address(self, partner):
        self.ensure_one()
        result = super()._match_address(partner=partner)
        zip_found = False
        if self.zip_ids:
            for zip_id in self.zip_ids:
                if (partner.zip or '').upper() >= zip_id.zip_from.upper() \
                   and (partner.zip or '').upper() <= zip_id.zip_to.upper():
                    zip_found = True
                    break
        return result or zip_found
