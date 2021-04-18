import os
import os.path
import base64
import glob
import sys
import logging
from odoo import api, fields, models

logger = logging.getLogger(__name__)


class Notification(models.TransientModel):
    _name = "notification"

    name = fields.Char("Notification", size=128)


class Generate(models.TransientModel):
    _name = "generate.image"

    image_path = fields.Char("Image/File Location")
    field_id = fields.Many2one("ir.model.fields", "Image/File target")
    success = fields.Integer("Success")
    failed = fields.Integer("Failed")

    @api.multi
    def generate_image(self):
        files_in_dir = os.listdir(self.image_path)
        success = 0
        failed = 0
        for files in files_in_dir:
            with open(self.image_path + "/" + files, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read())
                file_name = (files.split(".")[0]).replace(".", "/")
                file_name = file_name.replace("_", "/")
                products = self.env["product.template"].search([("name", "=", file_name)])

                if products:
                    if self.field_id.name == "image":
                        products.write({self.field_id and self.field_id.name or "image": encoded_string})
                        logger.info("Product image successfully updated : %s", files)
                        success += 1
                    elif self.field_id.name == "files":
                        products.write({
                            "files": [(0, 0, {
                                "name": files,
                                "datas": encoded_string,
                                "datas_fname": files,
                                "res_model": "product.template",
                                "type": "binary",
                                })]
                            })
                        logger.info("Product file successfully updated : %s", files)
                        success += 1
                else:
                    logger.warn("Failed to import this image/file into product due to no product match: %s", files)
                    failed += 1
        self.write({"success": success, "failed": failed})
        logger.info("Image import/file finish. Success: %s; Failed: %s", success, failed)
        view_id = self.env["ir.ui.view"].search([("model", "=", "generate.image"), ("name", "=", "Notification")])
        return {
            "type": "ir.actions.act_window",
            "name": "Congratulations!",
            "res_model": "generate.image",
            "view_type": "form",
            "view_mode": "form",
            "view_id": view_id.id,
            "res_id": self.id,
            "target": "new",
            "nodestroy": True,
        }
