# -*- coding: utf-8 -*-
#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#################################################################################
# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    enable_invoice_customer_replacement = fields.Boolean(
        string='Enable Invoice Customer Replacement',
        readonly=False,
        related='company_id.enable_invoice_customer_replacement',
        help="Enable the invoice customer replacement in partner form.")

    invoice_replacement_customer_id = fields.Many2one(
        'res.partner', readonly=False,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        related='company_id.invoice_replacement_customer_id',
        string='Replacement Customer', change_default=True)
