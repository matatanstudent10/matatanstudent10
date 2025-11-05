# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class AssignTaskWizard(models.TransientModel):
    """Wizard para asignar tarea de envío a un repartidor"""
    _name = 'delivery_expenses.assign_task_wizard'
    _description = 'Asignar Tarea de Envío'

    # Context - se obtiene del contexto cuando se abre desde supplier.payment.receipt
    payment_receipt_id = fields.Many2one(
        'supplier.payment.receipt',
        required=True,
        readonly=True,
        help='El recibo de pago para el cual se está creando la tarea'
    )

    @api.model
    def default_get(self, fields_list):
        """Obtener el payment_receipt_id del contexto"""
        res = super().default_get(fields_list)
        if 'payment_receipt_id' not in res:
            active_id = self.env.context.get('active_id')
            active_model = self.env.context.get('active_model')
            if active_model == 'supplier.payment.receipt' and active_id:
                res['payment_receipt_id'] = active_id
        return res

    # Wizard fields
    assigned_user_id = fields.Many2one(
        'res.partner',
        string='Repartidor',
        required=True,
        domain=[('user_ids', '!=', False)],
        help='Selecciona el repartidor o mensajero que entregará el cheque'
    )
    deadline = fields.Date(
        string='Fecha Límite',
        required=True,
        default=lambda self: (datetime.now() + timedelta(days=3)).date(),
        help='Fecha máxima para completar la entrega'
    )

    @api.onchange('assigned_user_id')
    def _onchange_assigned_user(self):
        """Al cambiar el repartidor, sugerir deadline en 3 días"""
        if not self.deadline or self.deadline == fields.Date.today():
            self.deadline = (datetime.now() + timedelta(days=3)).date()

    def action_create_task(self):
        """Crear la tarea y asignarla al repartidor"""
        self.ensure_one()

        # Validar que no exista tarea activa para este recibo
        existing_task = self.env['delivery_expenses.payment_task'].search([
            ('payment_receipt_id', '=', self.payment_receipt_id.id),
            ('state', 'in', ['draft', 'in_progress']),
        ])

        if existing_task:
            raise ValidationError(
                f'Ya existe una tarea activa para este recibo: {existing_task.name}\n'
                f'Complétala o cancélala antes de crear una nueva.'
            )

        # Validar deadline no sea en el pasado
        if self.deadline < datetime.now().date():
            raise ValidationError('La fecha límite no puede ser en el pasado')

        # Crear la tarea
        task = self.env['delivery_expenses.payment_task'].create({
            'payment_receipt_id': self.payment_receipt_id.id,
            'assigned_user_id': self.assigned_user_id.id,
            'deadline': self.deadline,
            'state': 'in_progress',
        })

        # Retornar la vista de la tarea creada
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'delivery_expenses.payment_task',
            'res_id': task.id,
            'view_mode': 'form',
            'views': [(False, 'form')],
            'target': 'current',
        }
