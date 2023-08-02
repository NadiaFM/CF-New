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
    @http.route('/messenger_integration', type='http', auth='public', website=True, csrf=False)
    def verify(self, **kw):
        # # webhook verification
        # if kwargs.get("hub.mode") == "subscribe" and kwargs.get("hub.challenge"):
        #     if not kwargs.get("hub.verify_token") == "hello":
        #         return "Verification token mismatch", 403
        #     return kwargs["hub.challenge"], 200
        # return "Hello World", 200
        # # response_data = {"message": "Hello World"}

        # # return http.Response(json.dumps(response_data), status=200, content_type='application/json')
        # Parse the query params
        mode = kw.get('hub.mode')
        token = kw.get('hub.verify_token')
        challenge = kw.get('hub.challenge')

        # Replace 'config.verifyToken' with your actual verify token value
        verify_token = 'hello'

        # Check if a token and mode is in the query string of the request
        if mode and token:
            # Check the mode and token sent is correct
            if mode == 'subscribe' and token == verify_token:
                # Respond with the challenge token from the request
                print("WEBHOOK_VERIFIED")
                return Response(challenge, status=200)
            else:
                # Respond with '403 Forbidden' if verify tokens do not match
                return Response('Forbidden', status=403)
        else:
            # Respond with '400 Bad Request' if mode or token is missing
            return Response('Bad Request', status=400)



    @http.route('/', type='json', auth='public', methods=['POST'], csrf=False)
    @http.route('/messenger_integration', type='json', auth='public', methods=['POST'], csrf=False)
    def webhook(self, **kwargs):
        data = json.loads(request.httprequest.data)
        self.log(data)
        return Response('Ok', status=200)

    def log(self, message):
        # raise UserError(str(message))
        _logger.info(str(message))
        sys.stdout.flush()
