# -*- coding: utf-8 -*-
from odoo import fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools.misc import formatLang


class AccountMove(models.Model):
    _inherit = "account.move"

    allow_exceeding_credit_limit = fields.Boolean(
        string='Allow Exceeding Credit Limit?',
        tracking=True,
        help='Allow invoice with customer credit limit overrode',
        default=False)

    def action_post(self):
        if self.partner_id:
            immediate_payment = self.env.ref('account.account_payment_term_immediate', raise_if_not_found=False)
            if (not self.invoice_payment_term_id or self.invoice_payment_term_id.id != immediate_payment.id) \
               and self.company_id.restrict_invoices \
               and self.move_type == 'out_invoice':
                if not self.allow_exceeding_credit_limit and not self.partner_id.commercial_partner_id.allow_override:
                    company_currency_id = self.company_id.currency_id
                    current_invoice_amount = self.amount_total_signed
                    # balance = self.partner_id.commercial_partner_id.balance
                    credit_limit = self.partner_id.commercial_partner_id.credit_limit
                    available_credit_amount = self.partner_id.commercial_partner_id.available_credit_amount
                    credit = self.partner_id.commercial_partner_id.credit

                    # Si el cliente tiene límite de crédito mayor a 0
                    if available_credit_amount - current_invoice_amount < 0:
                        raise ValidationError(
                            _("Credit limit exceeded by this customer. Please, contact to your "
                              "\"Credit & Collection Department\".\n"
                              "\n    Credit Limit: %s"
                              "\n    Credit: %s"
                              "\n    Available Credit: %s")
                            % (formatLang(self.env, credit_limit, currency_obj=company_currency_id),
                               formatLang(self.env, credit, currency_obj=company_currency_id),
                               formatLang(self.env, available_credit_amount, currency_obj=company_currency_id)))
        return super(AccountMove, self).action_post()
