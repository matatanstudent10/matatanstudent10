# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import MissingError
import logging

_logger = logging.getLogger(__name__)


class SupplierPaymentReceiptExt(models.Model):
    """Extensión del modelo supplier.payment.receipt para gestionar tareas de envío"""
    _inherit = 'supplier.payment.receipt'

    # Computed field para detectar tarea activa (draft o in_progress)
    active_payment_task_id = fields.Many2one(
        'delivery_expenses.payment_task',
        string='Tarea de Envío Activa',
        compute='_compute_active_payment_task',
        readonly=True,
        help='La tarea de envío actualmente asignada a este recibo'
    )

    # Computed field para detectar cualquier tarea (incluyendo completadas)
    any_payment_task_id = fields.Many2one(
        'delivery_expenses.payment_task',
        string='Tarea de Envío',
        compute='_compute_any_payment_task',
        readonly=True,
        help='Cualquier tarea de envío asociada a este recibo (activa o completada)'
    )

    # Campo para referenciar el attachment de la prueba de entrega
    prueba_de_entrega_attachment_id = fields.Many2one(
        'ir.attachment',
        string='Archivo de Prueba de Entrega',
        readonly=True,
        help='Referencia al attachment de la prueba de entrega para acceso rápido'
    )


    def _compute_active_payment_task(self):
        """Encontrar la tarea activa para este recibo"""
        for record in self:
            task = self.env['delivery_expenses.payment_task'].search([
                ('payment_receipt_id', '=', record.id),
                ('state', 'in', ['draft', 'in_progress']),
            ], limit=1)
            record.active_payment_task_id = task.id if task else False

    def _compute_any_payment_task(self):
        """Encontrar cualquier tarea para este recibo (incluyendo completadas)"""
        for record in self:
            task = self.env['delivery_expenses.payment_task'].search([
                ('payment_receipt_id', '=', record.id),
            ], limit=1, order='id desc')  # Get most recent task
            record.any_payment_task_id = task.id if task else False

    def action_open_payment_task(self):
        """Abrir la tarea de envío asociada o crear una nueva"""
        self.ensure_one()

        # Si existe cualquier tarea (activa o completada), abrirla
        if self.any_payment_task_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'delivery_expenses.payment_task',
                'res_id': self.any_payment_task_id.id,
                'view_mode': 'form',
                'target': 'current',
            }
        else:
            # Si no existe, abrir el wizard para crear
            return {
                'type': 'ir.actions.act_window',
                'name': 'Crear Envío de Cheque',
                'res_model': 'delivery_expenses.assign_task_wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_payment_receipt_id': self.id,
                    'active_id': self.id,
                    'active_model': 'supplier.payment.receipt',
                }
            }

