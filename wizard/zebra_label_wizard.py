# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ZebraLabelWizard(models.TransientModel):
    _name = 'zebra.label.wizard'
    _description = 'Wizard para imprimir etiquetas Zebra'

    picking_id = fields.Many2one('stock.picking', string='Picking', required=True)
    num_packages = fields.Integer(string='Número de Paquetes', required=True, default=1,
                                   help='Cantidad de etiquetas a generar')
    printer_model = fields.Selection([
        ('zd230', 'Zebra (8x10 cm)'),
        ('zt411', 'Zebra ZT411 (4x6 inch)'),
        ('custom', 'Personalizado (4x6 inch)')
    ], string='Modelo de Impresora', default='zd230', required=True)

    def action_print_labels(self):
        """Genera el PDF con las etiquetas"""
        self.ensure_one()

        # Seleccionar el reporte según el modelo de impresora
        report_map = {
            'zd230': 'label_picking.action_report_zebra_label',
            'zt411': 'label_picking.action_report_zebra_label_zt411',
            'custom': 'label_picking.action_report_zebra_label_custom',
        }

        report_ref = report_map.get(self.printer_model, 'label_picking.action_report_zebra_label')

        # Duplicar el picking N veces según num_packages para generar N etiquetas
        picking_ids = [self.picking_id.id] * self.num_packages

        # Retornar reporte con los datos correctos
        return self.env.ref(report_ref).report_action(picking_ids)
