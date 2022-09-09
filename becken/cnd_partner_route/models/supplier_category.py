# -*- coding: utf-8 -*-
from odoo import models, fields


class SupplierCategory(models.Model):

    _name = 'supplier.category'
    _description = 'Supplier Category'

    name = fields.Char(index=True, translate=True)
