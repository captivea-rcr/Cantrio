# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
import base64, os
from io import BytesIO
from PyPDF2 import PdfFileMerger, PdfFileReader


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    project_name = fields.Char(track_visibility='onchange')
    purchase_order = fields.Char(string="Purchase Order", track_visibility='onchange')

    # @api.multi
    def print_quotation_attachment(self):

        order = self
        pfiles = []
        report = self.env.ref('sale.action_report_saleorder').sudo().render_qweb_pdf([int(self.id)])[0]
        pdf_content_stream = BytesIO(report)
        pfiles.append(pdf_content_stream)
        for line in order.order_line:
            if line.product_id.files:
                for file in line.product_id.files:
                    pfiles.append(BytesIO(base64.decodestring(file.datas)))

        merger = PdfFileMerger()
        for filename in pfiles:
            reader = PdfFileReader(filename)
            merger.append(reader, import_bookmarks=False)
        merger.write("/opt/odoo/odoo/document-output.pdf")
        with open("/opt/odoo/odoo/document-output.pdf", 'rb') as pdf_document:
            pdf_content = pdf_document.read()
        os.unlink("/opt/odoo/odoo/document-output.pdf")
        pdf_content_stream.close()

        filename = ''
        if order.state in ['draft', 'sent']:
            filename = 'Quotation ' + order.name + ' - ' + order.partner_id.name + ' - ' + order.project_name + '.pdf'
        else:
            filename = 'Order ' + order.name + ' - ' + order.partner_id.name + ' - ' + order.project_name + '.pdf'

        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'datas': base64.b64encode(pdf_content),
            'datas_fname': filename,
            'res_model': 'sale.order',
            'res_id': self.id,
            'type': 'binary',
        })
        return {
            'res_model': 'ir.actions.act_url',
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s' % (attachment.id) + '?download=true',
            'target': 'current',
        }


class Product(models.Model):
    _inherit = 'product.template'

    files = fields.Many2many('ir.attachment')


class Invoice(models.Model):
    _inherit = 'account.move'

    project_name = fields.Char(track_visibility='onchange')


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    product_image = fields.Binary('Product Image', related="product_id.image_1920", store=False, readonly=True)