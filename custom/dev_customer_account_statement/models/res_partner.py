# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##############################################################################
from odoo import models, fields


class res_partner(models.Model):
    _inherit = 'res.partner'

    overdue_date = fields.Date('Overdue Date')
    aging_by = fields.Selection([('inv_date', 'Invoice Date'), ('due_date', 'Due Date')], string='Aging By')
