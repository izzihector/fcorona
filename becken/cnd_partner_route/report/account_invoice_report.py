# -*- coding: utf-8 -*-
from odoo import fields, models


class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    partner_route_id = fields.Many2one(
        'res.partner.route',
        string='Partner Route',
        help='The partner route is a field to categorize partners and can be used in sale report and invoice report.')

    supplier_category_id = fields.Many2one(
        'supplier.category',
        string='Supplier Category',
        help='The supplier category is a field to classify suppliers and can be used in sale report and invoice report.')

    def _select(self):
        return super(AccountInvoiceReport, self)._select() + \
            ",partner.route_id as partner_route_id,partner.supplier_category_id as supplier_category_id"

    def _group_by(self):
        return super(AccountInvoiceReport, self)._group_by() + ",partner.route_id,partner.supplier_category_id"
