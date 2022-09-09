# -*- coding: utf-8 -*-

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    enable_invoice_customer_replacement = fields.Boolean(
        string='Enable Invoice Customer Replacement',
        default=False,
        help="Enable the invoice customer replacement for this partner.")
