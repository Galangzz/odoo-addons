# from odoo import http


# class MrpRequest(http.Controller):
#     @http.route('/mrp_request/mrp_request', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/mrp_request/mrp_request/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('mrp_request.listing', {
#             'root': '/mrp_request/mrp_request',
#             'objects': http.request.env['mrp_request.mrp_request'].search([]),
#         })

#     @http.route('/mrp_request/mrp_request/objects/<model("mrp_request.mrp_request"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('mrp_request.object', {
#             'object': obj
#         })

