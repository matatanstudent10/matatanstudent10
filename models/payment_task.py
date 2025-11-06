# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
import logging
import base64

_logger = logging.getLogger(__name__)


class PaymentTask(models.Model):
    """
    Tarea de portal para el procesamiento de recibos de pago.
    Los usuarios cargan archivos de evidencia y marcan la tarea como completada.
    """
    _name = 'delivery_expenses.payment_task'
    _description = 'Tarea de Recibo de Pago'
    _inherit = ['mail.thread', 'portal.mixin']
    _order = 'deadline, id desc'

    name = fields.Char('Referencia', readonly=True, default='Nuevo', tracking=True)
    payment_receipt_id = fields.Many2one('supplier.payment.receipt', required=True, ondelete='cascade', tracking=True)
    assigned_user_id = fields.Many2one('res.partner', required=True, ondelete='cascade', domain=[('user_ids', '!=', False)], tracking=True)
    state = fields.Selection([('draft', 'En Borrador'), ('in_progress', 'En Progreso'), ('completed', 'Completada'), ('cancelled', 'Cancelada')], default='draft', tracking=True, copy=False)

    created_date = fields.Date(default=fields.Date.today, readonly=True, tracking=True)
    assigned_date = fields.Datetime(tracking=True)
    deadline = fields.Date(required=True, tracking=True)
    completed_date = fields.Datetime(readonly=True, copy=False)

    # Prueba de entrega (fotografía o documento)
    prueba_de_entrega = fields.Binary(
        string='Prueba de Entrega',
        attachment=True,
        help='Fotografía o documento que prueba la entrega del cheque (máximo 2MB)'
    )
    prueba_de_entrega_filename = fields.Char(
        string='Nombre del Archivo',
        help='Nombre del archivo de prueba de entrega'
    )

    # Related fields (read-only)
    supplier_id = fields.Many2one('res.partner', related='payment_receipt_id.partner_id', store=True, readonly=True)
    receipt_amount = fields.Monetary(related='payment_receipt_id.amount_total', store=True, readonly=True, currency_field='receipt_currency_id')
    receipt_currency_id = fields.Many2one('res.currency', related='payment_receipt_id.currency_id', store=True, readonly=True)
    receipt_date = fields.Date(related='payment_receipt_id.date', store=True, readonly=True)
    receipt_name = fields.Char(compute='_compute_receipt_name', store=True, readonly=True)
    supplier_name = fields.Char(compute='_compute_supplier_name', store=True, readonly=True)
    bank_name = fields.Char(compute='_compute_bank_name', store=True, readonly=True)
    check_amount_in_words = fields.Char(compute='_compute_check_amount_in_words', store=True, readonly=True)

    # Computed fields
    days_remaining = fields.Integer(compute='_compute_days_remaining', store=True)
    is_overdue = fields.Boolean(compute='_compute_is_overdue', store=True)

    _sql_constraints = [('unique_receipt_per_user', 'UNIQUE(payment_receipt_id, assigned_user_id)', 'Receipt can only be assigned once per user')]

    @api.depends('payment_receipt_id')
    def _compute_receipt_name(self):
        """Obtener nombre del recibo usando sudo para evitar problemas de acceso"""
        for record in self:
            if record.payment_receipt_id:
                record.receipt_name = record.payment_receipt_id.sudo().name
            else:
                record.receipt_name = ''

    @api.depends('supplier_id')
    def _compute_supplier_name(self):
        """Obtener nombre del supplier usando sudo para evitar problemas de acceso"""
        for record in self:
            if record.supplier_id:
                record.supplier_name = record.supplier_id.sudo().name
            else:
                record.supplier_name = ''

    @api.depends('payment_receipt_id')
    def _compute_bank_name(self):
        """Obtener nombre del banco del recibo"""
        for record in self:
            try:
                if record.payment_receipt_id:
                    journal = record.payment_receipt_id.sudo().journal_id
                    if journal and journal.bank_id:
                        record.bank_name = journal.bank_id.sudo().name
                    else:
                        record.bank_name = ''
                else:
                    record.bank_name = ''
            except:
                record.bank_name = ''

    @api.depends('payment_receipt_id')
    def _compute_check_amount_in_words(self):
        """Obtener el monto del cheque en letras"""
        for record in self:
            try:
                if record.payment_receipt_id:
                    record.check_amount_in_words = record.payment_receipt_id.sudo().check_amount_in_words or ''
                else:
                    record.check_amount_in_words = ''
            except:
                record.check_amount_in_words = ''

    @api.depends('deadline')
    def _compute_days_remaining(self):
        for record in self:
            if record.deadline:
                record.days_remaining = (record.deadline - datetime.now().date()).days
            else:
                record.days_remaining = 0

    @api.depends('deadline', 'state')
    def _compute_is_overdue(self):
        today = datetime.now().date()
        for record in self:
            if record.deadline:
                record.is_overdue = (record.deadline < today and record.state in ['draft', 'in_progress'])
            else:
                record.is_overdue = False

    @api.model
    def create(self, vals):
        """Generar referencia automáticamente y poner en progreso"""
        if not vals.get('name') or vals.get('name') == 'Nuevo':
            # Generar nombre basado en la fecha actual y número secuencial simple
            from datetime import datetime
            today = datetime.now().strftime('%Y%m%d')
            # Contar cuántas tareas se crearon hoy
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            count = self.search_count([('create_date', '>=', today_start)])
            vals['name'] = f"Tarea/{today}{str(count + 1).zfill(3)}"

        # Poner directamente en progreso
        if vals.get('state') is None:
            vals['state'] = 'in_progress'

        return super(PaymentTask, self).create(vals)

    def action_mark_completed(self):
        self.ensure_one()
        _logger.info(f'Marking task {self.name} as completed. Current state: {self.state}')

        if self.state not in ['draft', 'in_progress']:
            error_msg = f'Task is already {self.state}'
            _logger.warning(error_msg)
            raise ValidationError(error_msg)

        if not self.prueba_de_entrega:
            error_msg = 'Please upload the proof of delivery before completing'
            _logger.warning(f'{error_msg} for task {self.name}')
            raise ValidationError(error_msg)

        try:
            # Crear attachment vinculado al supplier.payment.receipt
            attachment = self.env['ir.attachment'].create({
                'name': self.prueba_de_entrega_filename or f'Prueba_Entrega_{self.name}.jpg',
                'datas': self.prueba_de_entrega,
                'res_model': 'supplier.payment.receipt',
                'res_id': self.payment_receipt_id.id,
            })
            _logger.info(f'Created attachment: {attachment.name} (ID: {attachment.id})')

            # Crear el body del mensaje con la imagen incrustada
            attachment_filename = self.prueba_de_entrega_filename or f'Prueba_Entrega_{self.name}.jpg'
            is_image = attachment_filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp'))

            if is_image:
                # Para imágenes, mostrar preview en el body
                body = f"""
                <p><b>Comprobante de Entrega Recibido</b></p>
                <p><b>Tarea:</b> {self.name}</p>
                <p><b>Archivo:</b> {attachment_filename}</p>
                <br/>
                <img src="/web/image/{attachment.id}" style="max-width: 500px; max-height: 500px; border-radius: 8px;"/>
                """
            else:
                # Para otros archivos, solo mostrar referencia
                body = f"""
                <p><b>Comprobante de Entrega Recibido</b></p>
                <p><b>Tarea:</b> {self.name}</p>
                <p><b>Archivo adjunto:</b> {attachment_filename}</p>
                """

            # Postar mensaje en el tracking del recibo
            self.payment_receipt_id.message_post(
                body=body,
                message_type='comment',
                subtype_xmlid='mail.mt_comment'
            )
            _logger.info(f'Tracking message posted successfully')

            # Guardar referencia al attachment en el recibo (sin vincularlo automáticamente)
            self.payment_receipt_id.prueba_de_entrega_attachment_id = attachment.id
            _logger.info(f'Stored attachment reference in receipt')

            # Marcar como completada
            self.state = 'completed'
            self.completed_date = fields.Datetime.now()
            _logger.info(f'Task {self.name} completed successfully')

        except Exception as e:
            _logger.error(f'Error completing task {self.name}: {str(e)}', exc_info=True)
            raise ValidationError(f'Error completing task: {str(e)}')

    def action_cancel(self):
        self.ensure_one()
        if self.state == 'completed':
            raise ValidationError('Cannot cancel a completed task')
        self.state = 'cancelled'

    def action_back_to_draft(self):
        """Devolver tarea a estado borrador"""
        self.ensure_one()
        if self.state == 'completed':
            raise ValidationError('Cannot revert a completed task to draft')
        self.state = 'draft'

    def get_status_label(self):
        """Get human-readable status label"""
        labels = {
            'draft': 'En Borrador',
            'in_progress': 'En Progreso',
            'completed': 'Completada',
            'cancelled': 'Cancelada',
        }
        return labels.get(self.state, self.state)
