# -*- coding: utf-8 -*-
from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    restrict_sale_orders = fields.Boolean(
        string='Restrict Sale Orders',
        default=True,
        help="If marked, restrict confirm Sale Orders if the customer has exeeded the credit limit.")

    restrict_invoices = fields.Boolean(
        string='Restrict Customer Invoices',
        default=True,
        help="If marked, restrict confirm customer invoices if the customer has exeeded the credit limit.")

    restrict_transfers = fields.Boolean(
        string='Restrict Stock Transfers',
        default=True,
        help="If marked, restrict validate stock transfers if the customer has exeeded the credit limit.")
