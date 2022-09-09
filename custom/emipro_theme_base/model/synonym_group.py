# -*- coding: utf-8 -*-
"""
    This model is used to manage group of synonyms
"""
from odoo import fields, models, api
from odoo.exceptions import UserError


class SynonymGroup(models.Model):
    """
    Class for Synonyms
    """
    _name = "synonym.group"
    _description = "Synonym Group"
    _order = "id desc"

    name = fields.Char(string='Synonyms Group', required=True,
                       help='Synonyms Group with comma separated keywords(Eg., Mobile,Smartphone,Cellphone)')
    website_id = fields.Many2one(string="Website", comodel_name="website",
                                 help="This group will only accessible for specified website. "
                                      "Accessible for all websites if not specified!")

    @api.model
    def create(self, vals):
        if vals.get('name', False):
            self.check_synonyms_validation(vals.get('name'))
        return super(SynonymGroup, self).create(vals)

    def write(self, vals):
        if vals.get('name', False):
            self.check_synonyms_validation(vals.get('name'))
        return super(SynonymGroup, self).write(vals)

    def check_synonyms_validation(self, synonyms=''):
        """ raise an error in two case:
         1) entered synonym(s) found in other synonym groups, or
         2) a synonym entered multiple times in a single synonym group"""
        synonym_groups = self.search([('id', '!=', self.id)]) if self else self.search([])
        synonym_list = [synm.strip().lower() for synm in synonyms.split(',')]
        for synm in synonym_list:
            if synonym_list.count(synm) > 1:
                raise UserError("You have entered '%s' multiple times.\n"
                                "\nMake sure that each synonym is entered only once!" % synm)
        if synonym_list and synonym_groups:
            for name in synonym_list:
                for synm_group in synonym_groups:
                    synonym_names = synm_group.name.split(',')
                    if name in [synm.strip().lower() for synm in synonym_names]:
                        raise UserError("Entered Synonym(s) matched with the existing group ID %s: "
                                        "\n%s\n\nYou can add synonyms in the existing group." %
                                        (synm_group.id, synm_group.name))
