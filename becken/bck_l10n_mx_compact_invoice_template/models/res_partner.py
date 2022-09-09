# -*- coding: utf-8 -*-
from odoo import models, api

ADDRESS_FIELDS = (
    'street', 'street2', 'zip', 'city', 'state_id', 'country_id',
    'l10n_mx_edi_colony',)


class Partner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def _address_fields(self):
        """Returns the list of address fields that are synced from the parent."""
        return list(ADDRESS_FIELDS)

    def _prepare_display_address(self, without_company=False):
        # JCT: Ocultar el nombre de la compañía en las direcciones
        without_company = True
        address_format, args = super()._prepare_display_address(without_company=without_company)
        return address_format, args
