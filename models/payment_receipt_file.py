# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class PaymentReceiptFile(models.Model):
    """Archivo adjunto para tareas de recibo de pago."""
    _name = 'delivery_expenses.payment_receipt_file'
    _description = 'Archivo de Recibo de Pago'
    _inherit = ['portal.mixin']
    _order = 'upload_date desc'

    payment_task_id = fields.Many2one('delivery_expenses.payment_task', required=True, ondelete='cascade')
    file_type = fields.Selection([('receipt', 'Recibo'), ('proof_of_delivery', 'Comprobante de Entrega'), ('invoice', 'Factura'), ('other', 'Otro')], required=True, default='other')
    attachment_id = fields.Many2one('ir.attachment', required=True, ondelete='cascade')

    file_name = fields.Char(related='attachment_id.name', store=True, readonly=True)
    file_size = fields.Integer(related='attachment_id.file_size', store=True, readonly=True)
    file_mimetype = fields.Char(related='attachment_id.mimetype', store=True, readonly=True)
    uploaded_by = fields.Many2one('res.partner', required=True, ondelete='restrict')
    upload_date = fields.Datetime(default=fields.Datetime.now, readonly=True)

    @api.model
    def create(self, vals):
        record = super().create(vals)

        # Validate file size
        if record.file_size and record.file_size > 10*1024*1024:
            raise ValidationError(f'El archivo es demasiado grande (máximo 10MB)')

        # Validate file type (more flexible)
        if record.file_mimetype:
            allowed_types = [
                'application/pdf',
                'image/jpeg',
                'image/jpg',
                'image/png',
                'image/gif',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'application/msword',
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'application/vnd.ms-excel'
            ]

            # Check if mimetype is allowed
            if record.file_mimetype not in allowed_types:
                _logger.warning(f'Attempting to upload file with MIME type: {record.file_mimetype}')
                # Only reject if it's clearly not an image, pdf, or doc
                if not any(record.file_mimetype.startswith(prefix) for prefix in ['image/', 'application/pdf']):
                    raise ValidationError(f'Tipo de archivo no permitido: {record.file_mimetype}')

        # Nota: El tracking con los archivos adjuntos se hace cuando se completa la tarea
        # en la función action_mark_completed() del modelo payment_task
        # Esto evita duplicados y asegura que todos los archivos se adjunten juntos

        return record
