# -*- coding: utf-8 -*-

from odoo import models, fields


class ResUsers(models.Model):
    _inherit = 'res.users'

    is_payment_user = fields.Boolean(
        string='Es Usuario de Tareas de Pago',
        default=False,
        help='Indica si el usuario puede ver y gestionar tareas de recibo de pago desde el portal.'
    )
