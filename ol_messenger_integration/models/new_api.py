from odoo import http
from odoo.http import request
from werkzeug.wrappers import Response
import json
import logging
_logger = logging.getLogger(__name__)

class WebhookController(http.Controller):
    @http.route('/webhook', type='http', auth='public', methods=['GET'], csrf=False)
    def handle_webhook(self, **post):
        print("Get")
        verify_token = post.get('hub.verify_token')
        hub_challenge = post.get('hub.challenge')
        _logger.info(str(hub_challenge))
        if verify_token == 'hello':
            return Response(hub_challenge, content_type='text/plain', status=200)
        
        else:
            return Response("Invalid verify token", content_type='text/plain', status=403)
            
    @http.route('/webhook', type='http', auth='public', methods=['POST'], csrf=False)
    def webhook(self, **kwargs):
        print('Post')
        data = request.httprequest.data
        body = data.decode('utf-8')
        new = eval(body)
        _logger.info(str(eval(body)))
        _logger.info(str(new))
        # print(body)
        # body = json.loads(data.decode('utf-8'))
        # if 'object' in body and body['object'] == 'page':
        if 'object' in new and new['object'] == 'page':
            entries = new['entry']
            for entry in entries:
                webhookEvent = entry['messaging'][0]
                # return request.make_response(webhookEvent)
                # senderPsid = webhookEvent['sender']['id']
                # print('sender PSID: {}'.format(senderPsid))
                if 'message' in webhookEvent:
                    # return Response(webhookEvent, status=200)
                    _logger.info(str(webhookEvent))
                # return Response('Ok', status=200)
                return Response(webhookEvent, status=200)
        else:
            return Response('Error', status=404)