# -*- coding: utf-8 -*-

from odoo import models, fields, api


class FetchResupplyData(models.TransientModel):
    _name = "fetch.resupply.data"
    _description = "Fetch Resupply Data"

    def generate_data(self):
        self.env["warehouse.resupply"].search([]).unlink()
        q = """
        SELECT sm.id, sm.product_id, sm.product_qty, sm.reference, sm.warehouse_id, so.id as order_id, sol.id as order_line_id, ot.code, sm.state
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
        for r in moves:
            vals = {
                "stock_move_id": r[0],
                "product_id": r[1],
                "quantity": r[2],
                "picking_number": r[3],
                "order_warehouse_id": r[4],
                "order_id": r[5],
                "order_line_id": r[6],
                "picking_id": False,
            }
            wr = self.env["warehouse.resupply"].create(vals)
            result.append(wr.id)
        action = self.env.ref('warehouse_resupply_plan.action_delivery_report').read()[0]
        action['domain'] = [('id', 'in', result)]
        return action
