# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import socket
import logging
import platform
import tempfile
import subprocess

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    picking_sequence_code = fields.Char(related='picking_type_id.sequence_code', string='Tipo de Operación')

    def action_print_zebra_label(self):
        """Abre wizard para solicitar número de paquetes"""
        # Validar que sea tipo PICK

        return {
            'name': 'Imprimir Etiquetas Zebra',
            'type': 'ir.actions.act_window',
            'res_model': 'zebra.label.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_picking_id': self.id}
        }

class ReportZebraLabel(models.AbstractModel):
    _name = 'report.label_picking.report_zebra_label_document'
    _description = 'Reporte de Etiquetas Zebra'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Genera los valores para el reporte con el número de paquetes"""
        # Si docids es None, intentar obtenerlo de data
        if not docids and data and isinstance(data, dict):
            docids = data.get('docids', [])

        docs = self.env['stock.picking'].browse(docids)

        # Obtener valores de data
        num_packages = 1
        label_width = '102mm'
        label_height = '152mm'

        if data and isinstance(data, dict):
            num_packages = data.get('num_packages', 1)
            label_width = data.get('label_width', '102mm')
            label_height = data.get('label_height', '152mm')

        return {
            'doc_ids': docids,
            'doc_model': 'stock.picking',
            'docs': docs,
            'data': data,
            'num_packages': num_packages,
            'label_width': label_width,
            'label_height': label_height,
        }
