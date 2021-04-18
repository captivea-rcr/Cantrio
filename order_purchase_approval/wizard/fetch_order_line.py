# -*- coding: utf-8 -*-

from odoo import models, fields, api


class FetchOrder(models.TransientModel):
    _name = "fetch.order.line"
    _description = "Fetch Order Line"

    def generate_data(self):
        self.env["order.line.warehouse"].search([]).unlink()
        q = """
        SELECT sm.id, sm.product_id, sm.product_qty, sm.reference, sm.warehouse_id, so.partner_id, so.project_name, so.id as order_id, sol.id as order_line_id, ot.code, sm.state, sm.date_expected
        FROM stock_move sm
        LEFT JOIN stock_picking_type ot on sm.picking_type_id = ot.id
        LEFT JOIN sale_order_line sol on sm.sale_line_id = sol.id
        LEFT JOIN sale_order so on sol.order_id = so.id
        WHERE sm.state in ('confirmed','partially_available')
        AND ot.code = 'outgoing';
        """
        self._cr.execute(q)
        moves = self._cr.fetchall()
        result = []
        # product_qty_dict = {}
        # for r in moves:
        #     if product_qty_dict.get(r[1]):
        #         product_qty_dict[r[1]] += r[2]
        #     else:
        #         product_qty_dict[r[1]] = r[2]

        # for k, v in product_qty_dict.items():
        #     vals = {
        #         "product_id": k,
        #         "total_order_qty": v,
        #     }
        #     olw = self.env["order.line.warehouse"].create(vals)
        #     result.append(olw.id)
        # action = self.env.ref('order_purchase_approval.action_order_line_warehouse').read()[0]
        # action['domain'] = [('id', 'in', result)]

        grouped_lines = {}
        for line in moves:
            if grouped_lines.get(line[1]):
                grouped_lines[line[1]].append(line)
            else:
                grouped_lines[line[1]] = [line]
        for product_id, lines in grouped_lines.items():
            detail_vals = [(0, 0, {
                "order_quantity": line[2],
                "partner_id": line[5],
                "project_name": line[6],
                "order_id": line[7],
                "expected_date": line[11],
            }) for line in lines]
            total_qty = sum([line[2] for line in lines])  # get sum of total order quantity for each product
            vals = {
                "product_id": product_id,
                "total_order_qty": total_qty,
                "order_detail_ids": detail_vals,
            }
            olw = self.env["order.line.warehouse"].create(vals)
            result.append(olw.id)
        action = self.env.ref('order_purchase_approval.action_order_line_warehouse').read()[0]
        action['domain'] = [('id', 'in', result)]
        return action
