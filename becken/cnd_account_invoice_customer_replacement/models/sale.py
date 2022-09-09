# -*- coding: utf-8 -*-
from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _prepare_invoice(self):
        self.ensure_one()

        invoice_vals = super(SaleOrder, self)._prepare_invoice()

        if self.company_id.enable_invoice_customer_replacement \
           and self.partner_id.commercial_partner_id.enable_invoice_customer_replacement:
            temp_partner_id = self.company_id.invoice_replacement_customer_id
            vals = {
                'l10n_mx_edi_usage': temp_partner_id.commercial_partner_id.l10n_mx_edi_usage,
                'l10n_mx_edi_payment_method_id': temp_partner_id.commercial_partner_id.l10n_mx_edi_payment_method_id,
                'invoice_payment_term_id': temp_partner_id.commercial_partner_id.property_payment_term_id,
            }
            invoice_vals.update(vals)

        return invoice_vals
