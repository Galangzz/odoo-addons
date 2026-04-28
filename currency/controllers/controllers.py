# from odoo import http


# class Currency(http.Controller):
#     @http.route('/currency/currency', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/currency/currency/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('currency.listing', {
#             'root': '/currency/currency',
#             'objects': http.request.env['currency.currency'].search([]),
#         })

#     @http.route('/currency/currency/objects/<model("currency.currency"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('currency.object', {
#             'object': obj
#         })

