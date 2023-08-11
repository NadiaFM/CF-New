from odoo import http
from odoo.http import request
from werkzeug.wrappers import Response
import json, requests
import logging
from werkzeug.utils import redirect
import base64



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
        # body = data.decode('utf-8')
        # _logger.info(body)
        # new = eval(body)
    
        # _logger.info(str(eval(body)))
        # _logger.info(str(new))
        # print(body)
        body = json.loads(data.decode('utf-8'))
        if 'object' in body and body['object'] == 'page':
        # if 'object' in new and new['object'] == 'page':
            entries = body['entry']
            for entry in entries:
                webhookEvent = entry['messaging'][0]
                # return request.make_response(webhookEvent)
                senderPsid = webhookEvent['sender']['id']
                # print('sender PSID: {}'.format(senderPsid))
                if 'message' in webhookEvent:
                    # return Response(webhookEvent, status=200)
                    _logger.info(str(webhookEvent))
                    url = "https://graph.facebook.com/{}?fields=id,name,email,picture&access_token={}".format(senderPsid, "EAA0GF4cZCxPkBO8Rn9ZAfeC8VF8lVtHyBjskmNheCZAmecwjA1vyRoZCgM8V1MtX0PvVmMKyJ748iKIxGaqiHQ93ZB8gq4v6FZAzg8ZAWROEooFUZBjLxZCc0mU5RN55wZBHWr5r5tHInS1cE0ZAQF56mronBR7AybAd5a5LF5WkRixZA4ZAyE8GqJXwTCbBySZBxAPxyb")
                    profile_data = requests.get(url)
                    sender_data = profile_data.json()
                    _logger.info(str(sender_data))
                    name = sender_data.get('name')
                    pic_url2 = sender_data.get('url')
                    _logger(str(pic_url2))
                    pic_url = sender_data['picture']['data']['url']
                    image_data = self.fetch_image_data(pic_url)
                    # _logger.info(str(image_data))

                    vals = {
                        'sender_id':senderPsid,
                        'name': name,
                        'image_1920': image_data,
                        'property_account_receivable_id': False,
                        'property_account_payable_id': False,
                    }
                    
                    existing_contact = http.request.env['res.partner'].sudo().search([('sender_id', '=', senderPsid)])
                    if existing_contact:
                        existing_contact.write(vals)
                    else:
                    # Create a new contact in Odoo
                        Contact = request.env['res.partner']
                        new_contact = Contact.sudo().create(vals)
                return Response(webhookEvent, status=200)
        else:
            return Response('Error', status=404)
        
    def fetch_image_data(self, image_url):
        response = requests.get(image_url)
        if response.status_code == 200:
            image_data = base64.b64encode(response.content)
            return image_data
        else:
            return None
