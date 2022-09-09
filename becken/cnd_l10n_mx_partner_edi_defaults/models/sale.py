# -*- coding: utf-8 -*-
from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _prepare_invoice(self):
        """
        Prepare the dict of values to create the new invoice for a sales order. This method may be
        overridden to implement custom invoice generation (making sure to call super() to establish
        a clean extension chain).
        """
        self.ensure_one()

        invoice_vals = super(SaleOrder, self)._prepare_invoice()

        # EDI Usage from Partner
        l10n_mx_edi_usage = False
        if self.partner_invoice_id.commercial_partner_id.l10n_mx_edi_usage:
            l10n_mx_edi_usage = self.partner_invoice_id.l10n_mx_edi_usage

        # Method from Partner
        l10n_mx_edi_payment_method_id = False
        # Facturas con Término de Pago igual a Inmediato, USO de CFDI = Por definir
        payment_term_immediate = self.env.ref('account.account_payment_term_immediate', raise_if_not_found=False)
        if self.payment_term_id != payment_term_immediate:
            l10n_mx_edi_payment_method_id = self.env.ref('l10n_mx_edi.payment_method_otros', raise_if_not_found=False)
        elif self.partner_invoice_id.commercial_partner_id.l10n_mx_edi_payment_method_id:
            l10n_mx_edi_payment_method_id = self.partner_invoice_id.commercial_partner_id.l10n_mx_edi_payment_method_id

        if l10n_mx_edi_usage:
            vals = {
                'l10n_mx_edi_usage': l10n_mx_edi_usage
            }
            invoice_vals.update(vals)

        if l10n_mx_edi_payment_method_id:
            vals = {
                'l10n_mx_edi_payment_method_id': l10n_mx_edi_payment_method_id
            }
            invoice_vals.update(vals)

        return invoice_vals
