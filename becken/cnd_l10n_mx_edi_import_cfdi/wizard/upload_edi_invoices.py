# -*- coding: utf-8 -*-
from odoo import models, api, fields, _
from odoo.exceptions import UserError

import base64
from io import BytesIO
import zipfile
from odoo.tools.osutil import tempdir
from lxml.objectify import fromstring
from odoo.tools.xml_utils import _check_with_xsd
from pathlib import Path
import os
import itertools
from operator import itemgetter
import logging

_logger = logging.getLogger(__name__)


MAX_FILE_SIZE = 100 * 1024 * 1024  # in megabytes


class UploadCorrectInvoices(models.TransientModel):
    _name = 'upload.correct.invoices'
    _description = 'Import Correct Invoices'

    invoice_upload_ids = fields.One2many(
        comodel_name='import.account.invoice',
        inverse_name='upload_correct_invoices_id',
        string='Invoices Uploaded',
        readonly=True)
    invoice_upload_count = fields.Integer(string='Invoice count', compute='_get_invoice_count')

    @api.onchange('invoice_upload_ids')
    def _get_invoice_count(self):
        self.invoice_upload_count = len(self.invoice_upload_ids.filtered(lambda invoice: invoice.xml_error is False))

    def action_ok(self):
        new_invoice_ids = []
        for invoice_upload_id in self.invoice_upload_ids:
            if not invoice_upload_id.xml_error:
                # Crear al partner si no existe
                if not invoice_upload_id.partner_id:
                    # Volver a buscar el cliente o proveedor, por si en esta misma carga se dió de alta ya,
                    # no darlo de alta dos veces
                    partner_id = self.env['res.partner'].search(
                        [('name', '=', invoice_upload_id.partner_name), ('vat', '=', invoice_upload_id.partner_vat)],
                        limit=1)
                    if not partner_id:
                        # country_mx = self.env['res.country'].search([('code', '=', 'mx')], limit=1)
                        country_mx = self.env.ref('base.mx')
                        values = {
                            'name': invoice_upload_id.partner_name,
                            'company_type': 'company',
                            'company_id': invoice_upload_id.company_id.id,
                            'vat': invoice_upload_id.partner_vat,
                            'property_payment_term_id': invoice_upload_id.partner_property_payment_term_id.id,
                            'property_supplier_payment_term_id':
                                invoice_upload_id.partner_property_supplier_payment_term_id.id,
                            'country_id': country_mx.id,
                        }
                        partner_id = self.env['res.partner'].create(values)
                    invoice_upload_id.partner_id = partner_id

                # Para no firmar la factura
                invoice_values = invoice_upload_id.with_context(
                    lang=invoice_upload_id.partner_id.lang)._prepare_invoice()
                context_invoice = dict(self.env.context, company_id=invoice_upload_id.company_id.id)

                # Crear la Factura
                new_invoice = self.env['account.move'].with_context(context_invoice).create(invoice_values)

                # Crear el adjunto XML
                if invoice_upload_id.xml_binary_content and invoice_upload_id.xml_file_name:
                    xml_invoice = self.env['ir.attachment'].create({
                        'name': invoice_upload_id.xml_file_name,
                        'type': 'binary',
                        'datas': invoice_upload_id.xml_binary_content,
                        'store_fname': invoice_upload_id.xml_file_name,
                        'res_model': 'account.move',
                        'res_id': new_invoice.id,
                        'mimetype': 'application/xml'
                    })
                    cfdi_3_3_edi = self.env.ref('l10n_mx_edi.edi_cfdi_3_3')
                    arr_edi_document_id = {
                        'edi_format_id': cfdi_3_3_edi.id,
                        'attachment_id': xml_invoice.id,
                        'state': 'sent',
                        }
                    arr_edi_document_ids = [(0, 0, arr_edi_document_id)]
                    new_invoice.write({'edi_document_ids': arr_edi_document_ids})

                # Crear el adjunto PDF
                new_invoice_ids.append(new_invoice.id)
                if invoice_upload_id.pdf_binary_content and invoice_upload_id.pdf_file_name:
                    self.env['ir.attachment'].create({
                        'name': invoice_upload_id.pdf_file_name,
                        'type': 'binary',
                        'datas': invoice_upload_id.pdf_binary_content,
                        'store_fname': invoice_upload_id.pdf_file_name,
                        'res_model': 'account.move',
                        'res_id': new_invoice.id,
                        'mimetype': 'application/pdf',
                    })

                # Asignar la cuenta de la factura en los "Apunte contables" ya existentes
                if invoice_upload_id.invoice_account_id:
                    account_type_receivable_id = self.env.ref('account.data_account_type_receivable')
                    account_type_payable_id = self.env.ref('account.data_account_type_payable')
                    journal_item_ids = new_invoice.line_ids.filtered(
                        lambda journal_item: journal_item.account_id.user_type_id in
                        [account_type_receivable_id, account_type_payable_id])
                    journal_item_ids.write({'account_id': invoice_upload_id.invoice_account_id.id})

        return {
            'name': _('Imported Invoices'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'nodestroy': True,
            'target': 'current',
            'domain': [('id', 'in', new_invoice_ids)],
        }


class ImportAccountInvoice(models.TransientModel):
    _name = 'import.account.invoice'
    _description = 'Import Account Invoice'

    invoice_type = fields.Selection(
        selection=[
            ('out_invoice', 'Customer Invoice'),
            ('out_refund', 'Customer Credit Note'),
            ('in_invoice', 'Vendor Bill'),
            ('in_refund', 'Vendor Credit Note'),
        ], string='Type', required=True, readonly=True,
        help="")
    invoice_date = fields.Date(
        string='Invoice/Bill Date',
        readonly=True, copy=False)
    xml_serie = fields.Char('Serie', readonly=True)
    xml_folio = fields.Char('Folio', readonly=True)
    upload_correct_invoices_id = fields.Many2one('upload.correct.invoices', string='Wizard Message', ondelete='cascade')
    rfc_supplier = fields.Text('RFC Emisor', required=True, readonly=True)
    rfc_customer = fields.Text('RFC Receptor', required=True, readonly=True)
    uuid = fields.Text('UUID', required=True, readonly=True)
    total_amount = fields.Monetary(string='Total amount', currency_field='currency_id')
    xml_error = fields.Boolean(string="Error", default=False)
    xml_state = fields.Text(string='Status')
    importation_type = fields.Selection(
        string='Importation Type',
        default='regular_invoices',
        required=True,
        selection=[('opening_balances', 'Opening Balances'), ('regular_invoices', 'Regular Invoices')],
        help='Regular Invoices - Import includes every line of the invoices.\n'
        'Opening Balances - Import only includes one summary invoice line.')
    # Invoice fields
    partner_id = fields.Many2one(
        'res.partner', readonly=True,
        string='Partner', change_default=True)
    currency_id = fields.Many2one(
        'res.currency', readonly=True,
        string='Currency')
    journal_id = fields.Many2one(
        'account.journal', string='Journal', required=True, readonly=True)
    invoice_line_ids = fields.One2many(
        'import.account.invoice.line', 'invoice_id', string='Invoice lines',
        copy=False, readonly=True)
    origin = fields.Char(
        string='Origin', readonly=True,
        help="The document(s) that generated the invoice.")
    company_id = fields.Many2one(
        'res.company',
        string='Company', store=True, readonly=True,
        related='journal_id.company_id', change_default=True)
    # xml_invoice_id = fields.Many2one('ir.attachment', string="Xml invoice", copy=False)
    xml_binary_content = fields.Binary(string="XML Binary", attachment=False, help="XML Binary Content")
    xml_file_name = fields.Char(string="XML File Name", readonly=True, help="XML File Name")
    # pdf_invoice_id = fields.Many2one('ir.attachment', string="Pdf invoice", copy=False)
    pdf_binary_content = fields.Binary(string="PDF Binary", attachment=False, help="PDF Binary Content")
    pdf_file_name = fields.Char(string="PDF File Name", readonly=True, help="PDF File Name")
    l10n_mx_edi_usage = fields.Selection([
        ('G01', 'Acquisition of merchandise'),
        ('G02', 'Returns, discounts or bonuses'),
        ('G03', 'General expenses'),
        ('I01', 'Constructions'),
        ('I02', 'Office furniture and equipment investment'),
        ('I03', 'Transportation equipment'),
        ('I04', 'Computer equipment and accessories'),
        ('I05', 'Dices, dies, molds, matrices and tooling'),
        ('I06', 'Telephone communications'),
        ('I07', 'Satellite communications'),
        ('I08', 'Other machinery and equipment'),
        ('D01', 'Medical, dental and hospital expenses.'),
        ('D02', 'Medical expenses for disability'),
        ('D03', 'Funeral expenses'),
        ('D04', 'Donations'),
        ('D05', 'Real interest effectively paid for mortgage loans (room house)'),
        ('D06', 'Voluntary contributions to SAR'),
        ('D07', 'Medical insurance premiums'),
        ('D08', 'Mandatory School Transportation Expenses'),
        ('D09', 'Deposits in savings accounts, premiums based on pension plans.'),
        ('D10', 'Payments for educational services (Colegiatura)'),
        ('P01', 'To define'),
    ], 'Usage', default='P01',
        help='Used in CFDI 3.3 to express the key to the usage that will '
        'gives the receiver to this invoice. This value is defined by the '
        'customer. \nNote: It is not cause for cancellation if the key set is '
        'not the usage that will give the receiver of the document.')
    invoice_user_id = fields.Many2one(
        'res.users',
        string='Salesperson',
        default=lambda self: self.env.user)
    invoice_team_id = fields.Many2one(
        'crm.team', string='Sales Team',
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')
    ref = fields.Char(string='Reference', size=32, readonly=True)
    # Partner Field
    partner_name = fields.Char(string="Partner Name")
    partner_vat = fields.Char(
        string='Tax ID',
        help="The Tax Identification Number. Complete it if the contact is subjected to government taxes. "
        "Used in some legal statements.")
    partner_property_payment_term_id = fields.Many2one(
        'account.payment.term', company_dependent=True,
        string='Payment Terms',
        help="This payment term will be used instead of the default one for sales orders and invoices")
    partner_property_supplier_payment_term_id = fields.Many2one(
        'account.payment.term', company_dependent=True,
        string='Vendor Payment Terms',
        help="This payment term will be used instead of the default one for purchase orders and vendor bills")
    invoice_account_id = fields.Many2one(
        'account.account', string='Invoice Account',
        check_company=True)
    lines_account_id = fields.Many2one(
        'account.account', string='Lines Account',
        check_company=True)

    def _prepare_invoice_data(self):
        self.ensure_one()

        company = self.env.company or self.company_id
        self = self.with_company(company).sudo()

        fpos_id = self.env['account.fiscal.position'].get_fiscal_position(self.partner_id.id)
        addr = self.partner_id.address_get(['delivery', 'invoice'])

        if self.importation_type == 'opening_balances':
            name = self.xml_serie + ' - ' + self.xml_folio
            narration = _("This invoice is opening balance invoice")
        else:
            name = '/'
            narration = _("This invoice was imported from his XML file")

        property_payment_term_id = False
        if self.invoice_type in ('out_invoice', 'out_refund'):
            property_payment_term_id = self.partner_property_payment_term_id.id
        elif self.invoice_type in ('in_invoice', 'in_refund'):
            property_payment_term_id = self.partner_property_supplier_payment_term_id.id

        return {
            'name': name,
            'invoice_date': self.invoice_date,
            'move_type': self.invoice_type,
            'partner_id': addr['invoice'],
            'partner_shipping_id': addr['delivery'],
            'currency_id': self.currency_id.id,
            'journal_id': self.journal_id.id,
            'invoice_origin': self.origin,
            'fiscal_position_id': fpos_id,
            'invoice_payment_term_id': property_payment_term_id,
            'narration': narration,
            'l10n_mx_edi_sign_required': False,
            'l10n_mx_edi_cfdi_uuid': self.xml_file_name,
            'l10n_mx_edi_usage': self.l10n_mx_edi_usage,
            'invoice_user_id': self.invoice_user_id.id,
            'team_id': self.invoice_team_id.id,
            'l10n_mx_edi_external_reference': name,
            # Para que no se timbre la factura al publicar
            'l10n_mx_edi_sign_required': False,
        }

    def _prepare_invoice_lines(self, fiscal_position):
        self.ensure_one()

        invoice_lines = []
        for line in self.invoice_line_ids:
            invoice_lines.append((0, 0, line._prepare_invoice_line(fiscal_position)))

        return invoice_lines

    def _prepare_invoice(self):
        invoice = self._prepare_invoice_data()
        invoice['invoice_line_ids'] = self._prepare_invoice_lines(invoice['fiscal_position_id'])
        return invoice


class ImportAccountInvoiceLine(models.TransientModel):
    _name = 'import.account.invoice.line'
    _description = 'Import Account Invoice Line'

    name = fields.Char(string='Label')
    price_unit = fields.Float(string='Unit Price', digits='Product Price')
    discount = fields.Float(string='Discount (%)', digits='Discount', default=0.0)
    quantity = fields.Float(
        string='Quantity',
        default=1.0, digits='Product Unit of Measure',
        help="The optional quantity expressed by this line, eg: number of product sold. "
             "The quantity is not a legal requirement but is very useful for some reports.")
    product_uom_id = fields.Many2one('uom.uom', string='Unit of Measure')
    tax_ids = fields.Many2many('account.tax', string='Taxes', help="Taxes that apply on the base amount")
    invoice_id = fields.Many2one(
        'import.account.invoice', string='Invoice',
        index=True, readonly=True, auto_join=True, ondelete="cascade",
        help="The invoice of this entry line.")

    def _prepare_invoice_line(self, fiscal_position):
        # Si hay descuento, convertirlo a porcentaje
        if self.discount > 0.0 and self.price_unit and abs(self.price_unit) > 0.0:
            self.discount = self.discount / (self.price_unit * self.quantity) * 100
        values = {
            'name': self.name,
            'price_unit': self.price_unit or 0.0,
            'discount': self.discount,
            'quantity': self.quantity,
            'product_uom_id': self.product_uom_id.id,
            'tax_ids': [(6, 0, self.tax_ids.ids)],
            'analytic_account_id': self.invoice_id.analytic_account_id.id,
            'analytic_tag_ids': [(6, 0, self.invoice_id.analytic_tag_ids.ids)],
        }
        # Esto porque si en el wizard se deja vacía la cuenta contable, que tome la por defecto del cliente
        # o de la configuración de contabilidad
        if self.invoice_id.lines_account_id:
            values['account_id'] = self.invoice_id.lines_account_id.id
        return values


def create_list_html(array):
    '''Convert an array of string to a html list.
    :param array: A list of strings
    :return: an empty string if not array, an html list otherwise.
    '''
    if not array:
        return ''
    msg = ''
    for item in array:
        msg += '<li>' + item + '</li>'
    return '<ul>' + msg + '</ul>'


class WizardAccountUploadEdiInvoices(models.TransientModel):
    _name = 'wizard.account.upload.edi.invoices'
    _description = 'Wizard to imposrt EDI invoices compressed in a zip file as opening balances'

    @api.model
    def _get_invoice_default_sale_team(self):
        return self.env['crm.team']._get_default_team_id()

    company_id = fields.Many2one(
        'res.company',
        string='Company', store=True, readonly=True,
        default=lambda self: self.env.user.company_id.id)
    journal_type = fields.Selection(
        string='Type',
        selection=[('purchase', 'Supplier Invoices'), ('sale', 'Customer Invoices')],
        default='purchase',
        help="Select if you are going to upload Customer Invoices or Supplier Invoices")
    journal_id = fields.Many2one(
        'account.journal', string='Journal', required=True,
        domain="[('type', '=', journal_type)]")
    zip_file = fields.Binary(
        string='Zip or Xml File', required=True,
        help='Compressed Zip file that contains the xml and pdf files of the edi invoices.')
    zip_filename = fields.Char('Zip or Xml File Name', copy=False)
    pdf_file = fields.Binary(
        string='Pdf File (optional)',
        help='Pdf representing the invoice of the xml file data (optional).')
    pdf_filename = fields.Char('Pdf File Name', copy=False)
    file_type = fields.Selection(
        string='File Type',
        default='zip',
        selection=[('zip', 'Zip'), ('xml', 'Xml')])
    create_partners_not_found = fields.Boolean(string='Create Partners not Found', default=False)
    new_partner_payment_term_id = fields.Many2one(
        'account.payment.term', string='New Partners Payment Terms')
    importation_type = fields.Selection(
        string='Importation Type',
        default='regular_invoices',
        required=True,
        selection=[('opening_balances', 'Opening Balances'), ('regular_invoices', 'Regular Invoices')],
        help='Regular Invoices - Import includes every line of the invoices.\n'
        'Opening Balances - Import only includes one summary invoice line.')
    invoice_user_id = fields.Many2one(
        'res.users',
        string='Salesperson',
        default=lambda self: self.env.user)
    invoice_team_id = fields.Many2one(
        'crm.team', string='Sales Team', default=_get_invoice_default_sale_team,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')
    ref = fields.Char(string='Reference', size=32)
    internal_type = fields.Selection(
        string='Internal Type',
        selection=[('payable', 'Supplier Invoices'), ('receivable', 'Customer Invoices')],
        default='payable',
        help="Select if you are going to upload Customer Invoices or Supplier Invoices")
    invoice_account_id = fields.Many2one(
        'account.account', string='Invoice Account',
        index=True, ondelete="cascade", check_company=True,
        domain="[('deprecated', '=', False), ('internal_type', '=', internal_type)]")
    lines_account_id = fields.Many2one(
        'account.account', string='Lines Account',
        index=True, ondelete="cascade", check_company=True)

    """
    LOS CAMPOS QUE ME PASÓ RAMON
        YA Tipo de factura: Cliente / Proveedor
        YA Tipo de Importacion: Saldos Iniciales / Factura regular
        YA Carga de Archivo: XML / Zip
        YA Plazo de pago: Seleccionable: Terminos de Pago
       XXX Cuenta de Factura: Seleccionable:  Cuentas de Tipo "A Pagar / A Cobrar"
        YA Diario: Seleccionable: De Venta / Compra
        YA Comercial: Seleccionable: Comercial, en el caso de facturas de clientes
       XXX Cuenta de linea: Cuenta de Ingreso o Gastos a la que se Cargaran en las lineas de Factura
       XXX Cuenta analitica de linea: Seleccionable
       XXX Etiquetas analiticas de linea: Seleccionable
        YA Equipo de ventas: En el caso de Facturas de Clientes
       XXX Referencia/Descripcion: En el caso de Facturas regulares de proveedores
    """

    @api.onchange('zip_file')
    def onchange_zip_file(self):
        self.ensure_one()
        if not self.zip_file:
            return
        filename, ext = os.path.splitext(self.zip_filename)
        ext = ext[1:].lower()
        if ext == 'zip':
            self.file_type = 'zip'
        elif ext == 'xml':
            self.file_type = 'xml'
        else:
            raise UserError(
                _('The file selected (%s) is no a zip nither xml file, please, select a zip or xml file.')
                % (self.zip_filename))

    @api.onchange('pdf_file')
    def onchange_pdf_file(self):
        self.ensure_one()
        if not self.pdf_filename:
            return
        filename, ext = os.path.splitext(self.pdf_filename)
        ext = ext[1:].lower()
        if ext != 'pdf':
            raise UserError(
                _('The file selected (%s) is no a pdf file, please, select a pdf file.') % (self.pdf_filename))

    @api.onchange('journal_type')
    def onchange_type(self):
        self.ensure_one()
        if self.journal_type == 'purchase':
            self.internal_type = 'payable'
        else:
            self.internal_type = 'receivable'
        self.journal_id = False

    def import_edi_invoices(self):
        invoices_to_upload = self.import_files()
        new_invoice_ids = []
        for invoice_to_upload in invoices_to_upload:
            # Si es una facura válida
            if invoice_to_upload:
                new_invoice_id = self.env['import.account.invoice'].create(invoice_to_upload)
                new_invoice_ids.append(new_invoice_id.id)

        values = {
            'invoice_upload_ids': [
                (6, 0, new_invoice_ids),
            ],
        }
        message_id = self.env['upload.correct.invoices'].create(values)
        return {
            'name': _('Invoices List'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'upload.correct.invoices',
            # pass the id
            'res_id': message_id.id,
            'target': 'new'
        }

    @api.model
    def l10n_mx_edi_get_xml_etree(self, cfdi=None):
        '''Get an objectified tree representing the cfdi.
        If the cfdi is not specified, retrieve it from the attachment.

        :param cfdi: The cfdi as string
        :return: An objectified tree
        '''
        # TODO helper which is not of too much help and should be removed
        self.ensure_one()
        if cfdi is None and self.l10n_mx_edi_cfdi:
            cfdi = base64.decodebytes(self.l10n_mx_edi_cfdi)
        # return fromstring(bytes(cfdi, encoding='utf-8')) if cfdi else None
        return fromstring(cfdi) if cfdi else None
        # data = etree.fromstring(bytes(r.text, encoding='utf-8'))

    @api.model
    def l10n_mx_edi_get_tfd_etree(self, cfdi):
        '''Get the TimbreFiscalDigital node from the cfdi.

        :param cfdi: The cfdi as etree
        :return: the TimbreFiscalDigital node
        '''
        if not hasattr(cfdi, 'Complemento'):
            return None
        attribute = 'tfd:TimbreFiscalDigital[1]'
        namespace = {'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital'}
        node = cfdi.Complemento.xpath(attribute, namespaces=namespace)
        return node[0] if node else None

    def _group_by_taxes(self, invoice_line_list):
        # Sort students data by `class` key.
        invoice_line_list = sorted(invoice_line_list, key=itemgetter('tax_ids'))

        # La unidad debe ser: H87 Pieza
        uom_id = self.env.ref('uom.product_uom_unit')

        # Display data grouped by `class`
        new_invoice_line_list = []
        for key, value in itertools.groupby(invoice_line_list, key=itemgetter('tax_ids')):
            new_invoice_line_dict = {}
            new_invoice_line_dict['tax_ids'] = key
            new_invoice_line_dict['name'] = 'Saldos Iniciales'
            new_invoice_line_dict['product_uom_id'] = uom_id.id
            new_invoice_line_dict['quantity'] = 1
            new_invoice_line_dict['price_unit'] = 0
            discount = 0.0
            for i in value:
                new_invoice_line_dict['price_unit'] += i.get('price_unit') * i.get('quantity')
                discount += i.get('discount')

            if discount > 0.0:
                new_invoice_line_dict['discount'] = discount
            new_invoice_line_list.append(new_invoice_line_dict)

        return new_invoice_line_list

    @api.model
    def import_files(self):
        zip_data = base64.decodebytes(self.zip_file)
        fp = BytesIO()
        fp.write(zip_data)

        if not fp:
            raise Exception(_("No file sent."))

        attachment = self.env.ref('l10n_mx_edi.xsd_cached_cfdv33_xsd', False)
        xsd_datas = base64.b64decode(attachment.datas) if attachment else b''

        company_vat = self.env.company.vat
        # Si el archivo a procesar en un ZIP
        if self.file_type == 'zip':
            with zipfile.ZipFile(fp, "r") as z:
                # Variable para validar si el archivo zip contiene archivos xml o no
                xml_files_content = False
                for zf in z.filelist:
                    # Procesar SIN DESCOMPRIMIR EL ARCHIVO ZIP
                    if zf.filename.lower().endswith('.xml'):
                        xml_files_content = True

                    if zf.file_size > MAX_FILE_SIZE:
                        raise UserError(_("File '%s' exceed maximum allowed file size!") % zf.filename)

                if xml_files_content is False:
                    raise UserError(_("File does not contains xml files compressed!"))

                with tempdir() as temp_invoices_dir:
                    try:
                        z.extractall(temp_invoices_dir)
                    except Exception as e:
                        raise UserError(_("Error unzipping '%s' file: %s") % (zf.filename, e))

                    xml_files = []
                    for filename in Path(temp_invoices_dir).rglob('*.xml'):
                        xml_files.append(filename)

                    result = []
                    for xml_file_path in xml_files:
                        xml_file = open(xml_file_path, "r", encoding='utf-8', errors='replace')
                        xml_filename = os.path.basename(xml_file_path)
                        # No tomar en cuenta los archivos ocultos, por ejemplo los ocultos que comprime MAC,
                        # que en realidad no son xml
                        if xml_filename[0] != '.':
                            cfdi = xml_file.read().encode('utf-8', errors='replace')
                            result.append(self.process_xml_content(cfdi, xsd_datas, xml_file_path, company_vat))
                    return result
        # Si el archivo a procesar en un XML
        elif self.file_type == 'xml':
            result = []
            cfdi = base64.decodebytes(self.zip_file)
            result.append(self.process_xml_content(cfdi, xsd_datas, self.zip_filename, company_vat))
            return result

    def process_xml_content(self, cfdi, xsd_datas, xml_file_path, company_vat):
        tree = self.l10n_mx_edi_get_xml_etree(cfdi)
        xml_file_name = os.path.basename(xml_file_path)

        # Validar que el xml corresponde a la factura y es un xml válido
        if xsd_datas:
            try:
                with BytesIO(xsd_datas) as xsd:
                    _check_with_xsd(tree, xsd)
            except (IOError, ValueError):
                raise UserError(_("The xsd file to validate the XML structure was not found"))
            except Exception as e:
                raise UserError(_('The CFDI generated is not valid.') + str(e))
        else:
            raise UserError(_("The xsd file to validate the XML structure was not found"))

        # if already signed, extract uuid
        tfd_node = self.l10n_mx_edi_get_tfd_etree(tree)

        if tfd_node is not None:
            invoice_date = tree.get('Fecha', tree.get('Fecha'))[:10] or str(fields.Date.today())
            invoice_currency = tree.get('Moneda', tree.get('moneda'))
            xml_serie = tree.get('Serie', tree.get('Serie')) or ''
            xml_folio = tree.get('Folio', tree.get('Folio')) or ''
            # I=Ingreso, E=Egreso, T=Traslado, P=Pago N=Nómina
            tipo_comprobante = tree.get('TipoDeComprobante', tree.get('TipoDeComprobante')) or ''

            invoice_currency_id = self.env['res.currency'].search([('name', '=', invoice_currency)]).id
            if not invoice_currency_id:
                xml_error = True
                xml_state = _(
                    'The currency "%s" does not exist or is not active in your database') % invoice_currency

            rfc_supplier = tree.Emisor.get('Rfc', tree.Emisor.get('Rfc'))
            name_supplier = tree.Emisor.get('Nombre', tree.Emisor.get('Nombre'))

            rfc_customer = tree.Receptor.get('Rfc', tree.Receptor.get('Rfc'))
            name_customer = tree.Receptor.get('Nombre', tree.Receptor.get('Nombre'))
            # TODO: Qué hacer con el uso de CFDI
            invoice_cfdi_use = tree.Receptor.get('UsoCFDI', tree.Emisor.get('UsoCFDI'))

            xml_error = False
            xml_state = _("Ready to Import XML!")

            if self.journal_type == 'sale':
                if tipo_comprobante == 'I':
                    invoice_type = 'out_invoice'
                elif tipo_comprobante == 'E':
                    invoice_type = 'out_refund'
                # Si el xml no es de tipo Ingreso ni Egreso
                else:
                    return False

                if rfc_supplier != company_vat:
                    xml_error = True
                    xml_state = _(
                        'Sender VAT "%s" does not coincide with the VAT of your Company "%s"'
                        ) % (rfc_supplier, company_vat)

                generic_partner = False
                partner_id = False
                if rfc_customer == 'XAXX010101000' or rfc_customer == 'XEXX010101000':
                    generic_partner = True
                else:
                    partner_id = self.env['res.partner'].search([('vat', '=', rfc_customer)], limit=1)

            elif self.journal_type == 'purchase':
                if tipo_comprobante == 'I':
                    invoice_type = 'in_invoice'
                elif tipo_comprobante == 'E':
                    invoice_type = 'in_refund'
                # Si el xml no es de tipo Ingreso ni Egreso
                else:
                    return False

                if rfc_customer != company_vat:
                    xml_error = True
                    xml_state = _(
                        'Receiver "%s" VAT does not coincide with the VAT of your Company "%s"'
                        ) % (rfc_customer, company_vat)

                generic_partner = False
                partner_id = False
                if rfc_supplier == 'XAXX010101000' or rfc_supplier == 'XEXX010101000':
                    generic_partner = True
                else:
                    partner_id = self.env['res.partner'].search([('vat', '=', rfc_supplier)], limit=1)

            partner_name = False
            partner_vat = False
            partner_property_payment_term_id = False
            partner_property_supplier_payment_term_id = False
            if not partner_id or generic_partner:
                if self.create_partners_not_found or generic_partner:
                    if self.journal_type == 'sale':
                        partner_name = name_customer
                        partner_vat = rfc_customer
                        partner_property_payment_term_id = self.new_partner_payment_term_id.id
                        partner_property_supplier_payment_term_id = False
                    elif self.journal_type == 'purchase':
                        partner_name = name_supplier
                        partner_vat = rfc_supplier
                        partner_property_payment_term_id = False
                        partner_property_supplier_payment_term_id = self.new_partner_payment_term_id.id
                else:
                    xml_error = True
                    xml_state = _("The Invoice Receiver is not in the Customer catalog.")
            else:
                # Validar que no se repita el mismo Serie + Folio + Cliente
                condition = [
                    ('partner_id', '=', partner_id.id),
                    ('name', '=', xml_serie + ' - ' + xml_folio),
                    ('move_type', '=', invoice_type),
                ]
                reteated_invoice_id = self.env['account.move'].search(condition, limit=1)
                if reteated_invoice_id:
                    xml_error = True
                    xml_state = _("The invoice is already in your invoice catalog.")
                if partner_id:
                    if self.journal_type == 'sale' and partner_id.property_payment_term_id:
                        partner_property_payment_term_id = partner_id.property_payment_term_id.id
                        partner_property_supplier_payment_term_id = False
                    elif self.journal_type == 'purchase' and partner_id.property_supplier_payment_term_id:
                        partner_property_payment_term_id = False
                        partner_property_supplier_payment_term_id = partner_id.property_supplier_payment_term_id.id

            invoice_uuid = tfd_node.get('UUID')

            conceptos = tree.Conceptos.Concepto
            import_invoice_lines = []
            for concepto in conceptos:
                # ClaveProdServ="80131502" Cantidad="1" ClaveUnidad="E48"
                # Descripcion="RENTA SEPTIEMBRE 2019" ValorUnitario="44445.00" Importe="44445.00"
                # <cfdi:Concepto ClaveProdServ="80101511" ClaveUnidad="E48" Cantidad="1.00" Unidad="SERVICIO"
                #     NoIdentificacion="700" Descripcion="Servicio de asesoramiento en recursos humanos"
                #     ValorUnitario="2873.55" Importe="2873.55">
                line_name = concepto.get('Descripcion', concepto.get('Descripcion'))
                line_price_unit = float(concepto.get('ValorUnitario', concepto.get('ValorUnitario')))
                # Extraer el descuento
                line_discount = concepto.get('Descuento', concepto.get('Descuento'))
                if line_discount is None:
                    line_discount = 0.0
                else:
                    line_discount = float(line_discount)
                line_quantity = float(concepto.get('Cantidad', concepto.get('Cantidad')))
                line_product_uom_id = False
                line_tax_ids = False

                clave_unidad_xml = concepto.get('ClaveUnidad', concepto.get('ClaveUnidad'))
                condition = [
                    ('code', '=', clave_unidad_xml),
                    ('applies_to', '=', 'uom'),
                ]
                # clave_unidad = self.env['l10n_mx_edi.product.sat.code'].search(condition)
                clave_unidad = self.env['product.unspsc.code'].search(condition)
                if not clave_unidad:
                    xml_error = True
                    xml_state = _("SAT code '%s' non-existent in the catalog!") % clave_unidad_xml

                condition = [
                    ('unspsc_code_id', '=', clave_unidad.id),
                ]
                uom_id = self.env['uom.uom'].search(condition, limit=1)

                if not uom_id:
                    xml_error = True
                    xml_state = _("There is no Unit of Measurement with the SAT key '%s'!") % clave_unidad_xml
                else:
                    line_product_uom_id = uom_id.id

                # Validar si existen Traslados o no en la línea, la línea de abajo marca error si no hay
                arr_tax_ids = []
                if hasattr(concepto, 'Impuestos') and hasattr(concepto.Impuestos, 'Traslados'):
                    impuestos_traslados = concepto.Impuestos.Traslados.Traslado

                    for impuesto_traslado in impuestos_traslados:
                        tax_key = impuesto_traslado.get('Impuesto', impuesto_traslado.get('Impuesto'))
                        tax_type = impuesto_traslado.get('TipoFactor', impuesto_traslado.get('TipoFactor'))
                        tasa_o_cuota = impuesto_traslado.get('TasaOCuota', impuesto_traslado.get('TasaOCuota'))
                        if tasa_o_cuota is None:
                            tasa_o_cuota = 0.0
                        tax_amount = float(tasa_o_cuota) * 100

                        # TODO: Si el impuesto no tiene TasaOCuota NO LO ESTOY AGREGANDO
                        # Ejemplo: <cfdi:Traslado Base="690.00" Impuesto="002" TipoFactor="Exento"/>
                        if self.journal_type == 'sale':
                            type_tax_use = 'sale'
                        elif self.journal_type == 'purchase':
                            type_tax_use = 'purchase'

                        condition = [
                            ('l10n_mx_cfdi_tax_key', '=', tax_key),
                            ('l10n_mx_tax_type', '=', tax_type),
                            ('amount', '=', tax_amount),
                            ('amount_type', '=', 'percent'),
                            ('type_tax_use', '=', type_tax_use),
                        ]
                        tax_id = self.env['account.tax'].search(condition, limit=1)
                        if not tax_id:
                            xml_error = True
                            xml_state = _(
                                "Missing tax. Type: Transfer, Factor Type: %s, Tax: %s, Rate or Fee: %s."
                                ) % (tax_type, tax_key, tasa_o_cuota)
                        else:
                            arr_tax_ids.append(tax_id.id)

                # Validar si existen Retenciones o no en la línea, la línea de abajo marca error si no hay
                if hasattr(concepto, 'Impuestos') and hasattr(concepto.Impuestos, 'Retenciones'):
                    impuestos_retenciones = concepto.Impuestos.Retenciones.Retencion

                    for impuesto_retencion in impuestos_retenciones:
                        tax_key = impuesto_retencion.get('Impuesto', impuesto_retencion.get('Impuesto'))
                        tax_type = impuesto_retencion.get('TipoFactor', impuesto_retencion.get('TipoFactor'))
                        tasa_o_cuota = impuesto_retencion.get('TasaOCuota', impuesto_retencion.get('TasaOCuota'))
                        amount = float(impuesto_retencion.get('Importe', impuesto_retencion.get('Importe')))
                        if tasa_o_cuota is not None:
                            if self.journal_type == 'sale' or amount > 0.0 and self.journal_type == 'purchase':
                                tax_amount = float(
                                    impuesto_retencion.get('TasaOCuota', impuesto_retencion.get('TasaOCuota'))) * 100

                                if self.journal_type == 'sale':
                                    type_tax_use = 'sale'
                                elif self.journal_type == 'purchase':
                                    type_tax_use = 'purchase'

                                condition = [
                                    ('l10n_mx_cfdi_tax_key', '=', tax_key),
                                    ('l10n_mx_tax_type', '=', tax_type),
                                    ('amount', '=', -tax_amount),
                                    ('amount_type', '=', 'percent'),
                                    ('type_tax_use', '=', type_tax_use),
                                ]
                                tax_id = self.env['account.tax'].search(condition, limit=1)
                                if not tax_id:
                                    xml_error = True
                                    xml_state = _(
                                        "Missing tax. Type: Retention, Factor Type: %s, Tax: %s, Rate or Fee: %s."
                                        ) % (tax_type, tax_key, tasa_o_cuota)
                                else:
                                    arr_tax_ids.append(tax_id.id)
                arr_tax_ids.sort()
                line_tax_ids = [(6, 0, arr_tax_ids)]

                dict_invoice_line = {
                    'name': line_name,
                    'price_unit': line_price_unit,
                    'discount': line_discount,
                    'quantity': line_quantity,
                    'product_uom_id': line_product_uom_id,
                    'tax_ids': line_tax_ids,
                }
                import_invoice_lines.append(dict_invoice_line)

            xml_binary_content = False
            pdf_binary_content = False
            pdf_file_name = False

            if not xml_error:
                xml_binary_content = base64.b64encode(cfdi)
                if self.file_type == 'xml':
                    pdf_file_name = self.pdf_filename
                    pdf_binary_content = self.pdf_file
                elif self.file_type == 'zip':
                    pdf_file_path = str(xml_file_path)[:-3] + 'pdf'
                    if os.path.isfile(pdf_file_path):
                        if xml_state == _("Ready to Import XML!"):
                            xml_state = _('Ready to Import XML and PDF!')
                        pdf_file_name = os.path.basename(pdf_file_path)

                        with open(pdf_file_path, 'rb') as f:
                            bin_data = f.read()
                            pdf_binary_content = base64.b64encode(bin_data)

            # Reemplazar esta condicional por si las facturas son de "Saldos Iniciales" o no
            if self.importation_type == 'opening_balances':
                import_invoice_lines = self._group_by_taxes(import_invoice_lines)
                origin = _("Initial Balance Import (%s)") % xml_file_name
            else:
                origin = _("Regular Invoice Import (%s)") % xml_file_name

            new_import_invoice_lines = []
            for import_invoice_line in import_invoice_lines:
                new_import_invoice_lines.append((0, 0, import_invoice_line))

            if partner_id:
                partner_id = partner_id.id
            invoice_dict = {
                'invoice_type': invoice_type,
                'invoice_date': invoice_date,
                'xml_serie': xml_serie,
                'xml_folio': xml_folio,
                'rfc_supplier': rfc_supplier,
                'rfc_customer': rfc_customer,
                'uuid': invoice_uuid,
                'currency_id': invoice_currency_id,
                'total_amount': tree.get('Total', tree.get('total')),
                'xml_error': xml_error,
                'xml_state': xml_state,
                'journal_id': self.journal_id.id,
                'partner_id': partner_id,
                'xml_binary_content': xml_binary_content,
                'xml_file_name': xml_file_name,
                'pdf_binary_content': pdf_binary_content,
                'pdf_file_name': pdf_file_name,
                'invoice_line_ids': new_import_invoice_lines,
                'l10n_mx_edi_usage': invoice_cfdi_use,
                'invoice_user_id': self.invoice_user_id.id,
                'invoice_team_id': self.invoice_team_id.id,
                'analytic_account_id': self.analytic_account_id.id,
                'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
                'ref': self.ref,
                'importation_type': self.importation_type,
                'origin': origin,
                'partner_name': partner_name,
                'partner_vat': partner_vat,
                'partner_property_payment_term_id': partner_property_payment_term_id,
                'partner_property_supplier_payment_term_id': partner_property_supplier_payment_term_id,
                'invoice_account_id': self.invoice_account_id.id,
                'lines_account_id': self.lines_account_id.id,
            }

            return invoice_dict
