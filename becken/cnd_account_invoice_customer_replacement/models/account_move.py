# -*- coding: utf-8 -*-
from odoo import fields, api, models


class AccountMove(models.Model):
    _inherit = "account.move"

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

            temp_partner_id = self.company_id.invoice_replacement_customer_id

            # EDI Usage from Temp Partner
            if temp_partner_id.commercial_partner_id.is_company \
               and temp_partner_id.commercial_partner_id.l10n_mx_edi_usage:
                self.l10n_mx_edi_usage = temp_partner_id.commercial_partner_id.l10n_mx_edi_usage

            # Method from Temp Partner
            if temp_partner_id.commercial_partner_id.is_company \
               and temp_partner_id.commercial_partner_id.l10n_mx_edi_payment_method_id:
                self.l10n_mx_edi_payment_method_id = temp_partner_id.commercial_partner_id.l10n_mx_edi_payment_method_id

            # Payment Term from Partner
            if temp_partner_id.commercial_partner_id.property_payment_term_id:
                self.invoice_payment_term_id = temp_partner_id.commercial_partner_id.property_payment_term_id

    @api.depends('partner_id')
    @api.onchange('partner_id')
    def _onchange_partner_id2(self):
        '''Set the payment l10n_mx_edi_usage on the sale order as the first of the selected partner.
        '''
        # OVERRIDE
        temp_partner_id = self.company_id.invoice_replacement_customer_id
        if self.partner_id and self.company_id.enable_invoice_customer_replacement \
           and self.partner_id.commercial_partner_id.enable_invoice_customer_replacement:
            self.replace_original_partner(temp_partner_id)

        if self.partner_id and self.company_id.enable_invoice_customer_replacement \
           and self.temp_partner_id.commercial_partner_id.enable_invoice_customer_replacement:
            self.return_original_partner()

    def _l10n_mx_edi_create_cfdi_values(self):
        self.ensure_one()
        values = super(AccountMove, self)._l10n_mx_edi_create_cfdi_values()

        if self.partner_id and self.company_id.enable_invoice_customer_replacement \
           and self.partner_id.commercial_partner_id.enable_invoice_customer_replacement:
            values.update({'customer': self.company_id.invoice_replacement_customer_id})
            values.update(self._get_external_trade_values(values))
        return values
