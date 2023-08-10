from odoo import models, fields

class WebhookData(models.Model):
    _inherit = 'res.partner'

    sender_id = fields.Char(string='Sender ID')
