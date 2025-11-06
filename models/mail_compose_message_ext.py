# -*- coding: utf-8 -*-

from odoo import models, api, fields
import logging

_logger = logging.getLogger(__name__)


class MailComposeMessageExt(models.TransientModel):
    """Extensión de mail.compose.message para adjuntar prueba de entrega automáticamente"""
    _inherit = 'mail.compose.message'

    @api.onchange('model', 'res_id')
    def _onchange_model_res_id(self):
        """Adjuntar prueba de entrega cuando se cambia el modelo o el res_id"""

        # Si es un email desde supplier.payment.receipt
        if self.model == 'supplier.payment.receipt' and self.res_id:
            receipt = self.env['supplier.payment.receipt'].browse(self.res_id)

            # Si existe prueba de entrega
            if receipt.prueba_de_entrega_attachment_id:
                proof_attachment = receipt.prueba_de_entrega_attachment_id

                # Verificar que no esté ya en los adjuntos
                if proof_attachment.id not in self.attachment_ids.ids:
                    # Adjuntar el archivo
                    self.attachment_ids = [(4, proof_attachment.id)]
                    _logger.info(f'Adjuntado automáticamente (onchange): {proof_attachment.name}')

    @api.model
    def default_get(self, fields_list):
        """Override default_get para adjuntar cuando se abre el wizard"""
        result = super().default_get(fields_list)

        # Si viene desde supplier.payment.receipt
        if result.get('model') == 'supplier.payment.receipt' and result.get('res_id'):
            receipt = self.env['supplier.payment.receipt'].browse(result['res_id'])

            # Si existe prueba de entrega
            if receipt.prueba_de_entrega_attachment_id:
                proof_attachment = receipt.prueba_de_entrega_attachment_id

                # Agregar a los attachment_ids
                result['attachment_ids'] = [(4, proof_attachment.id)]
                _logger.info(f'Adjuntado automáticamente (default_get): {proof_attachment.name}')

        return result

    def action_send_mail(self):
        """Override para adjuntar prueba de entrega antes de enviar (backup final)"""

        # Si es un email desde supplier.payment.receipt
        if self.model == 'supplier.payment.receipt' and self.res_id:
            receipt = self.env['supplier.payment.receipt'].browse(self.res_id)

            # Si existe prueba de entrega
            if receipt.prueba_de_entrega_attachment_id:
                proof_attachment = receipt.prueba_de_entrega_attachment_id

                # Verificar que no esté ya en los adjuntos
                if proof_attachment.id not in self.attachment_ids.ids:
                    # El attachment ya existe y tiene el contenido en datas
                    # Solo agregar la referencia
                    self.attachment_ids = [(4, proof_attachment.id)]
                    _logger.info(f'Adjuntado automáticamente al enviar: {proof_attachment.name}')

        # Ejecutar el método original
        return super().action_send_mail()
