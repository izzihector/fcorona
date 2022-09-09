from odoo import models


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    def _prepare_invoice_values(self, order, name, amount, so_line):
        self.ensure_one()

        invoice_vals = super(SaleAdvancePaymentInv, self)._prepare_invoice_values(order, name, amount, so_line)

        vals = {
            'l10n_mx_edi_sign_required': order.partner_invoice_id.commercial_partner_id.l10n_mx_edi_sign_required,
            'l10n_mx_edi_payment_sign_required': order.partner_invoice_id.commercial_partner_id.l10n_mx_edi_sign_required,
        }
        invoice_vals.update(vals)

        return invoice_vals
