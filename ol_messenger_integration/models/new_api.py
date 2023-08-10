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
        body = data.decode('utf-8')
        new = eval(body)
        # _logger.info(str(eval(body)))
        # _logger.info(str(new))
        # print(body)
        # body = json.loads(data.decode('utf-8'))
        # if 'object' in body and body['object'] == 'page':
        if 'object' in new and new['object'] == 'page':
            entries = new['entry']
            for entry in entries:
                webhookEvent = entry['messaging'][0]
                # return request.make_response(webhookEvent)
                senderPsid = webhookEvent['sender']['id']
                # print('sender PSID: {}'.format(senderPsid))
                if 'message' in webhookEvent:
                    # return Response(webhookEvent, status=200)
                    _logger.info(str(webhookEvent))
                    url = "https://graph.facebook.com/{}?fields=id,name,email,picture&access_token={}".format(senderPsid, "EAA0GF4cZCxPkBOwDZBDm92wHtUCgVVuXYTM6NbtkXMzEeQ5wyzeEqhCGsMdeqSeoDjDAH07GZBkWSoCBKPqTZBr6XEbcPb04Lrr4KkbHafeC7rzhqMiZCIKHG0fYSyU6XZA3jgMsQNOqJlu4dm5O9RN3R9qsT009oZAE3yeXu6svFVfOJMmG7bAH5kZCMU2FqGve")
                    profile_data = requests.get(url)
                    sender_data = profile_data.json()
                    _logger.info(str(sender_data))
                    request.session['sender_data'] = sender_data
                    name = sender_data.get('name')
                    _logger.info(str(name))
                    pic_url = sender_data['picture']['data']['url']
                    image_data = self.fetch_image_data(pic_url)
                    _logger.info(str(image_data))

                    vals = {
                        'sender_id':senderPsid,
                        'name': name,
                        'image_1920': image_data,
                        'property_account_receivable_id': False,
                        'property_account_payable_id': False,
                        # Other contact fields you want to populate
                    }
                    
                    existing_contact = http.request.env['res.partner'].sudo().search([('sender_id', '=', senderPsid)])
                    if existing_contact:
                        existing_contact.write(vals)
                    else:
                    # Create a new contact in Odoo
                        Contact = request.env['res.partner']
                        new_contact = Contact.sudo().create(vals)
                    # sdata = request.session.get('sender_data')
                    # _logger.info(str(sdata))
                    # WebhookData.create({
                    #     'sender': sender_data,
                    #     'message': webhookEvent,
                    #     # Assign other field values as needed
                    # })
                    # redirect_url = "/display_data?sender_data={}".format(sender_data)
            
            # Redirect the user to the second controller
                    # return redirect(redirect_url)
                # return Response('Ok', status=200)
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

# class ProfileController(http.Controller):
#     @http.route('/display_data', type='http', auth='public', methods=['GET'], csrf=False)
#     def display_data(self, **post):
#         # Retrieve sender_data from session
#         # sender_data = request.session.get('sender_data')
#         # print(sender_data)
#         # _logger.info(str(sender_data))
#         # return Response(str(sender_data), content_type='text/plain',status=200)
#         # sender_data = request.params.get('sender_data')
        
#         # _logger.info("Retrieved sender_data from URL parameters: %s", sender_data)
        
#         # return Response(str(sender_data), content_type='text/plain', status=200)

#         webhook_data = http.request.env['ol_messenger_integration.webhook_data'].search([])
#         # Process webhook_data as needed
        
#         return http.request.render('ol_messenger_integration.messenger_integeration_view.xml', {
#             'webhook_data': webhook_data
#         })

        # Now you can use sender_data to display on a webpage or process further
        # ...
