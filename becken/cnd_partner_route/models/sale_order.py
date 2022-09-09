# -*- coding: utf-8 -*-
from odoo import models, fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    partner_route_id = fields.Many2one(
        'res.partner.route',
        string='Route',
        related='partner_id.route_id',
        store=True,
        readonly=True,
        help='The partner route is a field to categorize partners and can be used in sale report and invoice report.')
