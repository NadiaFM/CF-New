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
    @http.route('/get_message_from_facebook',  type='http', methods=['GET'],auth='public', website=True,csrf=False)
    def verify(self, **kw):
       
        mode = http.request.params.get('hub.mode')
        token = http.request.params.get('hub.verify_token')
        challenge = http.request.params.get('hub.challenge')
           
        verify_token = 'integration'
       
        if mode == 'subscribe' and token == verify_token:
            # Respond with the challenge token from the request
            print("WEBHOOK_VERIFIED")
            return Response(challenge, status=200)
        else:
            # Respond with '403 Forbidden' if verify tokens do not match
            return Response('Forbidden', status=403)
     

    @http.route('/get_message_from_facebook', type='json', auth='public', methods=['POST'], csrf=False)
    def webhook(self, **kwargs):
        data = request.httprequest.data
        body = json.loads(data.decode('utf-8'))
        if 'object' in body and body['object'] == 'page':
            entries = body['entry']
            for entry in entries:
                webhookEvent = entry['messaging'][0]
                senderPsid = webhookEvent['sender']['id']
                print('sender PSID: {}'.format(senderPsid))
                if 'message' in webhookEvent:
                   
                    _logger.info(str(webhookEvent))
                    # _logger.info(str(webhookEvent['message']))
                    # _logger.info(str(webhookEvent['sender']))

            # Return a successful response (200 status code) to Facebook, as it expects a 200 response for successful handling of the webhook.
            return Response('Ok', status=200)
        else:
            # Return a 404 response if the request doesn't have the expected 'object' key.
            return Response('Error', status=404)
