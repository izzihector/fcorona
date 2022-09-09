# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools.misc import formatLang


class CreditLimitAlertSaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = 'sale.order'

    allow_exceeding_credit_limit = fields.Boolean(
        string='Allow Exceeding Credit Limit?',
        tracking=True,
        default=False)

    def action_confirm(self):
        # Término de pago inmediato
        immediate_payment = self.env.ref('account.account_payment_term_immediate')

        # Verificar si es un pedido web
        # Si no tiene payment.transaction, verificar el límite de crédito, si el pedido viene del ecommerce,
        # no restringir
        if (not self.payment_term_id or self.payment_term_id.id != immediate_payment.id) \
           and self.company_id.restrict_sale_orders \
           and not ('website_id' in self and self.website_id is not False):
            # Si el campo de permitir con límite excedido o vencido, pues ya no importa nada.
            if not self.allow_exceeding_credit_limit and not self.partner_id.commercial_partner_id.allow_override:
                today = fields.Date.today()
                company_currency_id = self.company_id.currency_id
                current_sale_amount = self.env['res.currency']._convert(
                    self.amount_total, self.company_id.currency_id, self.currency_id, today)
                # balance = self.partner_id.commercial_partner_id.balance
                credit_limit = self.partner_id.commercial_partner_id.credit_limit
                available_credit_amount = self.partner_id.commercial_partner_id.available_credit_amount
                credit = self.partner_id.commercial_partner_id.credit

                # Si el cliente tiene límite de crédito mayor a 0
                if available_credit_amount - current_sale_amount < 0:
                    raise ValidationError(
                        _("Credit limit exceeded by this customer. Please, contact to your "
                          "\"Credit & Collection Department\".\n"
                          "\n    Credit Limit: %s"
                          "\n    Credit: %s"
                          "\n    Available Credit: %s")
                        % (formatLang(self.env, credit_limit, currency_obj=company_currency_id),
                           formatLang(self.env, credit, currency_obj=company_currency_id),
                           formatLang(self.env, available_credit_amount, currency_obj=company_currency_id)))

        res = super(CreditLimitAlertSaleOrder, self).action_confirm()
        return res

    @api.onchange('allow_exceeding_credit_limit')
    def udpate_stock_moves(self):
        for sale in self._origin:
            for stock_picking in sale.picking_ids:
                stock_picking.write({'allow_exceeding_credit_limit': sale.allow_exceeding_credit_limit})
