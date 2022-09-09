# -*- coding: utf-8 -*-
from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    route_id = fields.Many2one(
        'res.partner.route',
        string='Route',
        help='The partner route is a field to categorize partners and can be used in sale report and invoice report.')

    supplier_category_id = fields.Many2one(
        'supplier.category',
        string='Category',
        help='The supplier category is a field to classify suppliers and can be used in sale report and invoice report.')
