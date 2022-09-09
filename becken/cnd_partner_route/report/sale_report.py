# -*- coding: utf-8 -*-
from odoo import fields, models


class SaleReport(models.Model):
    _inherit = "sale.report"

    partner_route_id = fields.Many2one(
        'res.partner.route',
        string='Route',
        help='The partner route is a field to categorize partners and can be used in sale report and invoice report.')

    supplier_category_id = fields.Many2one(
        'supplier.category',
        string='Supplier Category',
        help='The supplier category is a field to classify suppliers and can be used in sale report and invoice report.')

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        fields['partner_route_id'] = ", partner.route_id AS partner_route_id"
        fields['supplier_category_id'] = ", partner.supplier_category_id AS supplier_category_id"
        groupby += ', partner.route_id, partner.supplier_category_id'
        return super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)
