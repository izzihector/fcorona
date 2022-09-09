# -*- coding: utf-8 -*-
from odoo import models, fields


class AccountMove(models.Model):
    _inherit = 'account.move'

    partner_route_id = fields.Many2one(
        'res.partner.route',
        string='Route',
        related='partner_id.route_id',
        store=True,
        readonly=True,
        help='The partner route is a field to categorize partners and can be used in sale report and invoice report.')

    supplier_category_id = fields.Many2one(
        'supplier.category',
        string='Supplier Category',
        related='partner_id.supplier_category_id',
        store=True,
        readonly=True,
        help='The supplier category is a field to classify suppliers and can be used in sale report and invoice report.')
