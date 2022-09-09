# -*- coding: utf-8 -*-
from odoo import models, fields


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    temp_partner_id = fields.Many2one(
        'res.partner',
        string='Temporal Customer', default=False)

    def replace_original_partner(self, replacement_partner_id):
        if not self.temp_partner_id:
            self.temp_partner_id = self.partner_id
            self.partner_id = replacement_partner_id

    def return_original_partner(self):
        if self.temp_partner_id:
            self.partner_id = self.temp_partner_id
            self.temp_partner_id = False
            # temp_partner_id = self.company_id.invoice_replacement_customer_id

    def _l10n_mx_edi_create_cfdi_values(self):
        self.ensure_one()
        values = super(AccountPayment, self)._l10n_mx_edi_create_cfdi_values()

        if self.partner_id and self.company_id.enable_invoice_customer_replacement \
           and self.partner_id.commercial_partner_id.enable_invoice_customer_replacement:
            values.update({'customer': self.company_id.invoice_replacement_customer_id})

        return values
