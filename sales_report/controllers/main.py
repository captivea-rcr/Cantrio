from odoo import fields, http, tools, _
from odoo.http import request, content_disposition
import base64, os
from io import BytesIO
from PyPDF2 import PdfFileMerger, PdfFileReader

class Quote(http.Controller):
    @http.route('/web/quote/<int:order_id>', type='http', auth='user')
    def index(self, order_id, **kw):
        if order_id:
            order = request.env['sale.order'].search([('id', '=', int(order_id))])
            pfiles = []
            report = request.env.ref('sale.action_report_saleorder').sudo().render_qweb_pdf([int(order_id)])[0]
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
            merger.write("document-output.pdf")
            with open("document-output.pdf", 'rb') as pdf_document:
                pdf_content = pdf_document.read()
            os.unlink("document-output.pdf")
            pdf_content_stream.close()

            filename = ''
            if order.state in ['draft', 'sent']:
                filename = 'Quotation '+order.name+' - '+order.partner_id.name+' - '+order.project_name+'.pdf'
            else:
                filename = 'Order '+order.name+' - '+order.partner_id.name+' - '+order.project_name+'.pdf'
            content_base64 = base64.b64decode(pdf_content)
            pdfhttpheaders = [('Content-Type', 'application/pdf'), ('X-Content-Type-Options', 'nosniff'),('Cache-Control', 'max-age=0'),
                                ('Content-Disposition', content_disposition(filename))]
            pdfhttpheaders.append(('Content-Length', len(content_base64)))
            return request.make_response(pdf_content, headers=pdfhttpheaders)
        

    