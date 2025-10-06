# -*- coding: utf-8 -*-
# from odoo import http


# class LabelPicking(http.Controller):
#     @http.route('/label_picking/label_picking', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/label_picking/label_picking/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('label_picking.listing', {
#             'root': '/label_picking/label_picking',
#             'objects': http.request.env['label_picking.label_picking'].search([]),
#         })

#     @http.route('/label_picking/label_picking/objects/<model("label_picking.label_picking"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('label_picking.object', {
#             'object': obj
#         })
