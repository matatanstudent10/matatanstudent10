# -*- coding: utf-8 -*-

from odoo import http
from odoo.exceptions import AccessError, MissingError, ValidationError
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.portal.controllers.portal import pager as portal_pager
from werkzeug.datastructures import FileStorage
import base64
import logging

_logger = logging.getLogger(__name__)


class PaymentReceiptPortal(CustomerPortal):
    """
    Portal controller for payment receipt task management.
    Extends CustomerPortal to provide portal user access to payment tasks.
    """

    def _prepare_portal_layout_values(self):
        """Agregar contadores de tareas de pago al layout del portal"""
        values = super()._prepare_portal_layout_values()
        user = request.env.user
        partner = user.partner_id

        try:
            payment_task_count = request.env['delivery_expenses.payment_task'].search_count([
                ('assigned_user_id', '=', partner.id)
            ])
        except:
            payment_task_count = 0

        values.update({
            'payment_task_count': payment_task_count,
        })

        return values

    @http.route(['/my/payment-tasks', '/my/payment-tasks/page/<int:page>'],
                auth='user', website=True)
    def portal_my_payment_tasks(self, page=1, sortby=None, **kwargs):
        """Display list of payment tasks assigned to current user"""
        partner = request.env.user.partner_id

        # Build search domain
        domain = [('assigned_user_id', '=', partner.id)]

        # Get filter parameter
        filterby = kwargs.get('filterby', 'in_progress')

        # Apply filters from request
        if filterby == 'all':
            # Show all tasks
            pass
        elif filterby == 'in_progress':
            domain.append(('state', '=', 'in_progress'))
        elif filterby == 'completed':
            domain.append(('state', '=', 'completed'))
        else:
            # Default: show in_progress (non-completed)
            domain.append(('state', 'in', ['in_progress']))

        # Search term
        if kwargs.get('search'):
            search_term = kwargs['search']
            domain.append('|')
            domain.append(('payment_receipt_id.name', 'ilike', search_term))
            domain.append(('supplier_id.name', 'ilike', search_term))

        # Sorting options
        SortMapping = {
            'deadline': 'deadline asc',
            'amount': 'receipt_amount desc',
            'status': 'state asc',
        }
        order = SortMapping.get(sortby, 'deadline asc')

        # Pagination
        PaymentTask = request.env['delivery_expenses.payment_task']
        payment_task_count = PaymentTask.search_count(domain)
        pager = portal_pager(
            url="/my/payment-tasks",
            url_args={'sortby': sortby, 'filterby': filterby, 'group_by': kwargs.get('group_by')} if sortby or filterby else None,
            total=payment_task_count,
            page=page,
            step=10,  # Tasks per page
        )
        offset = pager['offset']

        # Fetch tasks
        payment_tasks = PaymentTask.search(
            domain,
            order=order,
            limit=10,
            offset=offset
        )

        # Get grouping parameter
        group_by = kwargs.get('group_by', 'none')

        # Get all available banks from user's tasks for the dropdown
        all_tasks_for_banks = PaymentTask.search(
            [('assigned_user_id', '=', partner.id)],
            order='deadline asc'
        )
        available_banks = sorted(set(
            task.bank_name for task in all_tasks_for_banks if task.bank_name
        ))

        # Group tasks by bank if requested
        tasks_by_bank = {}
        if group_by == 'bank':
            for task in payment_tasks:
                bank = task.bank_name or 'Sin banco asignado'
                if bank not in tasks_by_bank:
                    tasks_by_bank[bank] = []
                tasks_by_bank[bank].append(task)
        else:
            # No grouping - all tasks in one group
            tasks_by_bank = {'all': payment_tasks}

        values = {
            'payment_tasks': payment_tasks,
            'tasks_by_bank': tasks_by_bank,
            'available_banks': available_banks,
            'group_by': group_by,
            'payment_task_count': payment_task_count,
            'pager': pager,
            'sortby': sortby,
            'filterby': filterby,
            'default_url': '/my/payment-tasks',
            # NO usar page_name - causaba breadcrumb a /task
            'searchbar_filters': {
                'all': {'label': 'Todas', 'domain': []},
                'in_progress': {'label': 'En Progreso', 'domain': [('state', '=', 'in_progress')]},
                'completed': {'label': 'Completadas', 'domain': [('state', '=', 'completed')]},
            },
        }

        return request.render('delivery_expenses.portal_payment_tasks', values)

    @http.route('/my/payment-tasks/<int:task_id>', auth='user', website=True)
    def portal_payment_task_detail(self, task_id, **kwargs):
        """Display payment task detail page"""
        try:
            payment_task = request.env['delivery_expenses.payment_task'].browse(task_id)

            # Check access: user can only see tasks assigned to them
            partner = request.env.user.partner_id
            if payment_task.assigned_user_id != partner:
                raise AccessError('You do not have permission to view this task')

            values = {
                'payment_task': payment_task,
                'page_name': 'payment_task',
            }

            return request.render('delivery_expenses.portal_payment_task_detail', values)

        except MissingError:
            raise http.request.not_found()
        except AccessError:
            raise http.request.redirect('/my/payment-tasks')

    @http.route('/my/payment-tasks/<int:task_id>/upload', auth='user', methods=['POST'],
                csrf=True, website=True)
    def portal_payment_task_upload_file(self, task_id, **kwargs):
        """Handle file upload for payment task"""
        payment_task = request.env['delivery_expenses.payment_task'].browse(task_id)

        # Check access
        partner = request.env.user.partner_id
        if payment_task.assigned_user_id != partner:
            raise AccessError('You do not have permission to upload files to this task')

        # Check task state
        if payment_task.state == 'completed':
            raise ValidationError('Cannot upload files to a completed task')

        # Get uploaded files
        files = request.httprequest.files.getlist('files')
        file_type = request.httprequest.form.get('file_type', 'other')

        _logger.info(f'Attempting to upload {len(files)} files for task {task_id}')

        if not files or not any(file for file in files if file.filename):
            _logger.warning('No files provided for upload')
            return request.redirect(f'/my/payment-tasks/{task_id}')

        uploaded_count = 0
        error_messages = []

        for file in files:
            if not file or not file.filename:
                continue

            _logger.info(f'Processing file: {file.filename}, type: {file.content_type}')

            try:
                # Read file content
                file_content = file.read()
                file_size = len(file_content)

                # Validate file size
                if file_size > 10 * 1024 * 1024:  # 10 MB
                    error_messages.append(f'{file.filename}: Archivo muy grande (máximo 10MB)')
                    _logger.warning(f'File {file.filename} too large: {file_size} bytes')
                    continue

                if file_size == 0:
                    error_messages.append(f'{file.filename}: Archivo vacío')
                    _logger.warning(f'File {file.filename} is empty')
                    continue

                # Create attachment using sudo (portal users can upload files via controller)
                try:
                    attachment = request.env['ir.attachment'].sudo().create({
                        'name': file.filename,
                        'datas': base64.b64encode(file_content),
                        'mimetype': file.content_type or 'application/octet-stream',
                    })
                    _logger.info(f'Created attachment {attachment.id} for {file.filename}, MIME: {file.content_type}')
                except Exception as att_error:
                    error_msg = f'Error creando attachment para {file.filename}: {str(att_error)}'
                    _logger.error(error_msg)
                    error_messages.append(error_msg)
                    continue

                # Create payment receipt file record using sudo
                try:
                    payment_file = request.env['delivery_expenses.payment_receipt_file'].sudo().create({
                        'payment_task_id': payment_task.id,
                        'attachment_id': attachment.id,
                        'file_type': file_type,
                        'uploaded_by': partner.id,
                    })
                    _logger.info(f'Created payment file record {payment_file.id} for {file.filename}')
                    uploaded_count += 1
                except ValidationError as val_error:
                    error_msg = f'Validación fallida para {file.filename}: {str(val_error)}'
                    _logger.error(error_msg)
                    error_messages.append(error_msg)
                    # Eliminar el attachment que se creó pero falló la validación
                    try:
                        attachment.sudo().unlink()
                        _logger.info(f'Deleted attachment {attachment.id} due to validation error')
                    except:
                        pass
                    continue
                except Exception as record_error:
                    error_msg = f'Error creando registro para {file.filename}: {str(record_error)}'
                    _logger.error(error_msg)
                    error_messages.append(error_msg)
                    # Eliminar el attachment que se creó pero falló el registro
                    try:
                        attachment.sudo().unlink()
                        _logger.info(f'Deleted attachment {attachment.id} due to record error')
                    except:
                        pass
                    continue

            except Exception as e:
                error_msg = f'Error inesperado cargando {file.filename}: {str(e)}'
                _logger.error(error_msg, exc_info=True)
                error_messages.append(error_msg)
                continue

        _logger.info(f'Upload completed: {uploaded_count} files uploaded, {len(error_messages)} errors')

        # Redirect back with success message
        return request.redirect(f'/my/payment-tasks/{task_id}')

    @http.route('/my/payment-tasks/<int:task_id>/upload-proof', auth='user', methods=['POST'],
                csrf=True, website=True)
    def portal_payment_task_upload_proof(self, task_id, **kwargs):
        """Upload proof of delivery file"""
        _logger.info(f'Attempting to upload proof for task {task_id}')

        try:
            payment_task = request.env['delivery_expenses.payment_task'].browse(task_id)

            if not payment_task.exists():
                _logger.warning(f'Task {task_id} does not exist')
                raise MissingError('Task not found')

            # Check access
            partner = request.env.user.partner_id
            if payment_task.assigned_user_id != partner:
                raise AccessError('You do not have permission to upload files to this task')

            # Check task state
            if payment_task.state == 'completed':
                raise ValidationError('Cannot upload files to a completed task')

            # Get uploaded file
            file = request.httprequest.files.get('proof_file')

            _logger.info(f'Attempting to upload proof file for task {task_id}')

            if not file or not file.filename:
                _logger.warning('No file provided for proof upload')
                return request.redirect(f'/my/payment-tasks/{task_id}')

            try:
                # Read file content
                file_content = file.read()
                file_size = len(file_content)

                # Validate file size (2 MB max)
                if file_size > 2 * 1024 * 1024:  # 2 MB
                    _logger.warning(f'Proof file {file.filename} too large: {file_size} bytes')
                    return request.redirect(f'/my/payment-tasks/{task_id}')

                if file_size == 0:
                    _logger.warning(f'Proof file {file.filename} is empty')
                    return request.redirect(f'/my/payment-tasks/{task_id}')

                # Save proof to task
                payment_task.sudo().write({
                    'prueba_de_entrega': base64.b64encode(file_content),
                    'prueba_de_entrega_filename': file.filename
                })

                _logger.info(f'Proof of delivery uploaded successfully for task {task_id}: {file.filename}')

            except Exception as e:
                _logger.error(f'Error uploading proof for task {task_id}: {str(e)}', exc_info=True)
                return request.redirect(f'/my/payment-tasks/{task_id}')

        except (AccessError, ValidationError, MissingError) as e:
            _logger.error(f'Validation error uploading proof for task {task_id}: {str(e)}')
            return request.redirect(f'/my/payment-tasks/{task_id}')
        except Exception as e:
            _logger.error(f'Unexpected error uploading proof for task {task_id}: {str(e)}', exc_info=True)
            return request.redirect(f'/my/payment-tasks/{task_id}')

        # Redirect back with success message
        return request.redirect(f'/my/payment-tasks/{task_id}')

    @http.route('/my/payment-tasks/<int:task_id>/complete', auth='user', methods=['POST'],
                csrf=True, website=True)
    def portal_payment_task_complete(self, task_id, **kwargs):
        """Mark task as completed"""
        _logger.info(f'Attempting to complete task {task_id}')

        try:
            payment_task = request.env['delivery_expenses.payment_task'].browse(task_id)
            _logger.info(f'Task found: {payment_task.name}, state: {payment_task.state}')

            # Check if task exists
            if not payment_task.exists():
                _logger.warning(f'Task {task_id} does not exist')
                raise MissingError('Task not found')

            # Check access
            partner = request.env.user.partner_id
            _logger.info(f'Current partner: {partner.name}, assigned to: {payment_task.assigned_user_id.name}')

            if payment_task.assigned_user_id != partner:
                _logger.warning(f'Access denied: user {partner.name} is not assigned to task {task_id}')
                raise AccessError('You do not have permission to modify this task')

            # Check if has proof of delivery
            _logger.info(f'Task has proof of delivery: {bool(payment_task.prueba_de_entrega)}')
            if not payment_task.prueba_de_entrega:
                _logger.warning(f'Task {task_id} has no proof of delivery, cannot complete')
                raise ValidationError('Please upload the proof of delivery before completing')

            # Call action (use sudo to bypass access control for portal users)
            _logger.info(f'Calling action_mark_completed for task {task_id}')
            payment_task.sudo().action_mark_completed()
            _logger.info(f'Task {task_id} completed successfully')

            return request.redirect(f'/my/payment-tasks/{task_id}')

        except AccessError as ae:
            _logger.error(f'Access error completing task {task_id}: {str(ae)}')
            return request.redirect(f'/my/payment-tasks/{task_id}?error=access_denied')
        except ValidationError as ve:
            _logger.error(f'Validation error completing task {task_id}: {str(ve)}')
            return request.redirect(f'/my/payment-tasks/{task_id}?error=validation_failed')
        except MissingError as me:
            _logger.error(f'Task {task_id} not found: {str(me)}')
            raise http.request.not_found()
        except Exception as e:
            _logger.error(f'Unexpected error completing task {task_id}: {str(e)}', exc_info=True)
            return request.redirect(f'/my/payment-tasks/{task_id}?error=unexpected')

    @http.route('/my/payment-tasks/<int:task_id>/cancel', auth='user', methods=['POST'],
                csrf=True, website=True)
    def portal_payment_task_cancel(self, task_id, **kwargs):
        """Cancel task"""
        try:
            payment_task = request.env['delivery_expenses.payment_task'].browse(task_id)

            # Check access
            partner = request.env.user.partner_id
            if payment_task.assigned_user_id != partner:
                raise AccessError('You do not have permission to modify this task')

            # Call action (use sudo to bypass access control for portal users)
            payment_task.sudo().action_cancel()

            return request.redirect('/my/payment-tasks')

        except (AccessError, ValidationError):
            return request.redirect(f'/my/payment-tasks/{task_id}')
        except MissingError:
            raise http.request.not_found()

    @http.route('/my/payment-tasks/file/<int:file_id>/view', auth='user', website=True)
    def portal_payment_file_view(self, file_id, **kwargs):
        """View payment receipt file (preview for images, download for others)"""
        try:
            payment_file = request.env['delivery_expenses.payment_receipt_file'].browse(file_id)

            # Check access: user can only view files from their assigned tasks
            partner = request.env.user.partner_id
            if payment_file.payment_task_id.assigned_user_id != partner:
                raise AccessError('You do not have permission to view this file')

            attachment = payment_file.attachment_id.sudo()

            # Decode base64 data
            file_data = base64.b64decode(attachment.datas) if attachment.datas else b''

            # For images, show inline; for others, download
            mimetype = attachment.mimetype or 'application/octet-stream'
            is_image = mimetype.startswith('image/')

            disposition = 'inline' if is_image else 'attachment'

            return request.make_response(
                file_data,
                headers=[
                    ('Content-Type', mimetype),
                    ('Content-Disposition', f'{disposition}; filename="{attachment.name}"'),
                    ('Content-Length', str(len(file_data))),
                ]
            )

        except (AccessError, ValidationError) as e:
            _logger.error(f'Error viewing file: {str(e)}')
            return request.not_found()
        except MissingError:
            return request.not_found()
        except Exception as e:
            _logger.error(f'Unexpected error viewing file: {str(e)}')
            return request.not_found()

    @http.route('/my/payment-tasks/file/<int:file_id>/download', auth='user', website=True)
    def portal_payment_file_download(self, file_id, **kwargs):
        """Download payment receipt file"""
        try:
            payment_file = request.env['delivery_expenses.payment_receipt_file'].browse(file_id)

            # Check access: user can only download files from their assigned tasks
            partner = request.env.user.partner_id
            if payment_file.payment_task_id.assigned_user_id != partner:
                raise AccessError('You do not have permission to download this file')

            attachment = payment_file.attachment_id.sudo()

            # Decode base64 data
            file_data = base64.b64decode(attachment.datas) if attachment.datas else b''

            return request.make_response(
                file_data,
                headers=[
                    ('Content-Type', attachment.mimetype or 'application/octet-stream'),
                    ('Content-Disposition', f'attachment; filename="{attachment.name}"'),
                    ('Content-Length', str(len(file_data))),
                ]
            )

        except (AccessError, ValidationError) as e:
            _logger.error(f'Error downloading file: {str(e)}')
            return request.not_found()
        except MissingError:
            return request.not_found()
        except Exception as e:
            _logger.error(f'Unexpected error downloading file: {str(e)}')
            return request.not_found()
