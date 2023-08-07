from odoo import http
from odoo.http import request
from werkzeug.wrappers import Response
import json

class WebhookController(http.Controller):

    @http.route('/webhook', type='http', auth='public', methods=['GET', 'POST'], csrf=False)
    def handle_webhook(self, **post):
        if request.httprequest.method == 'GET':
            # Handle the webhook verification
            verify_token = post.get('hub.verify_token')
            # _logger.info(str(webhookEvent))
            # return Response(post.get('hub.verify_token'), content_type='text/plain', status=200)
            hub_challenge = post.get('hub.challenge')
            if verify_token == 'hello':
            # if verify_token == verify_token:

                return Response(hub_challenge, content_type='text/plain', status=200)
            else:
                return Response("Invalid verify token", content_type='text/plain', status=403)
        elif request.httprequest.method == 'POST':
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
