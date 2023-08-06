# messenger_integration/controllers.py

from odoo import http
from odoo.http import request , Response
import json
from odoo.exceptions import UserError
import os,sys
import logging
_logger = logging.getLogger(__name__)

class MessengerIntegrationController(http.Controller):

    # @http.route('/', type='http', auth='public', website=True, csrf=False)
    @http.route('/messenger_integration',  type='http', methods=['GET'],auth='public', website=True,csrf=False)
    def verify(self, **kw):
        raise UserError("hey")
        
        # # webhook verification
        # if kwargs.get("hub.mode") == "subscribe" and kwargs.get("hub.challenge"):
        #     if not kwargs.get("hub.verify_token") == "hello":
        #         return "Verification token mismatch", 403
        #     return kwargs["hub.challenge"], 200
        # return "Hello World", 200
        # # response_data = {"message": "Hello World"}

        # # return http.Response(json.dumps(response_data), status=200, content_type='application/json')
        # Parse the query params
        
        # mode = kw.get('hub.mode')
        # token = kw.get('hub.verify_token')
        # challenge = kw.get('hub.challenge')
        mode = http.request.params.get('hub.mode')
        token = http.request.params.get('hub.verify_token')
        challenge = http.request.params.get('hub.challenge')
        # raise UserError(mode)
        # _logger.info(str(webhookEvent))

        # Replace 'config.verifyToken' with your actual verify token value
        verify_token = 'hello'
        # raise UserError(verify_token)
        # Check if a token and mode is in the query string of the request
        # if mode and token:
            
        #     # Check the mode and token sent is correct
        if mode == 'subscribe' and token == verify_token:
            # Respond with the challenge token from the request
            print("WEBHOOK_VERIFIED")
            return Response(challenge, status=200)
        else:
            # Respond with '403 Forbidden' if verify tokens do not match
            return Response('Forbidden', status=403)
        # else:
        #     # Respond with '400 Bad Request' if mode or token is missing
        #     return Response('Bad Request', status=400)



    # @http.route('/', type='json', auth='public', methods=['POST'], csrf=False)
    @http.route('/messenger_integration', type='json', auth='public', methods=['POST'], csrf=False)
    def webhook(self, **kwargs):
        # data = json.loads(request.httprequest.data)
        # self.log(data)
        # return Response('Ok', status=200)
        data = request.httprequest.data
        body = json.loads(data.decode('utf-8'))
        if 'object' in body and body['object'] == 'page':
            entries = body['entry']
            for entry in entries:
                webhookEvent = entry['messaging'][0]
                # return str(webhookEvent)
                # return request.make_response(webhookEvent)
                senderPsid = webhookEvent['sender']['id']
                print('sender PSID: {}'.format(senderPsid))
                if 'message' in webhookEvent:
                    return Response(webhookEvent, status=200)
                    _logger.info(str(webhookEvent))
                    _logger.info(str(webhookEvent['message']))
                    _logger.info(str(webhookEvent['sender']))
                    # handleMessage(senderPsid, webhookEvent['message'])
                return Response('Ok', status=200)
        else:
            return Response('Error', status=404)

    def log(self, message):
        # raise UserError(str(message))
        _logger.info(str(message))
        sys.stdout.flush()

# class Sale_order(http.Controller):

#     @http.route(['/Sale-order-form'], type='http', auth="user", website=True, csrf=False)
#     def index(self, **post):
#         # product_list = request.env['product.product'].sudo().search([('is_phone','=',True)])
#         raise UserError(str(request.session['mode']))
#         return request.render('sh_portal_dashboard.sale_order_temp',{'product_list': product_list})