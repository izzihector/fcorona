# -*- coding: utf-8 -*-
from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    enable_invoice_customer_replacement = fields.Boolean(
        string='Enable Invoice Customer Replacement',
        default=False,
        help="Enable the invoice customer replacement in partner form.")

    invoice_replacement_customer_id = fields.Many2one(
        'res.partner',
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        string='Replacement Customer', change_default=True)
