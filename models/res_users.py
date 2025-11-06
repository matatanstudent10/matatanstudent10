# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    is_payment_user = fields.Boolean(
        string='Es Usuario de Tareas de Pago',
        default=False,
        help='Indica si el usuario puede ver y gestionar tareas de recibo de pago desde el portal.'
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Assign group when user is created with is_payment_user=True"""
        for vals in vals_list:
            if vals.get('is_payment_user'):
                # Get the group
                group = self.env.ref('supplier_payment_receipts.user_treasury_financial')
                if 'groups_id' not in vals:
                    vals['groups_id'] = []
                # Add group to the list
                vals['groups_id'].append((4, group.id))

        return super().create(vals_list)

    def write(self, vals):
        """Manage group assignment when is_payment_user changes"""
        result = super().write(vals)

        if 'is_payment_user' in vals:
            try:
                group = self.env.ref('supplier_payment_receipts.user_treasury_financial')

                for record in self:
                    if vals['is_payment_user']:
                        # Add group if not already assigned
                        if group not in record.groups_id:
                            record.write({'groups_id': [(4, group.id)]})
                            _logger.info(f'Assigned group {group.name} to user {record.name}')
                    else:
                        # Remove group if assigned
                        if group in record.groups_id:
                            record.write({'groups_id': [(3, group.id)]})
                            _logger.info(f'Removed group {group.name} from user {record.name}')
            except Exception as e:
                _logger.error(f'Error managing payment user groups: {str(e)}')

        return result
