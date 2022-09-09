# -*- coding: utf-8 -*-
from odoo import models, fields


class ResPartnerRoute(models.Model):

    _name = 'res.partner.route'
    _description = 'Partner Route'

    name = fields.Char(index=True, translate=True)
