from odoo.api import Environment, SUPERUSER_ID
from . import models
from . import wizards


def pre_init_hook(cr):
    env = Environment(cr, SUPERUSER_ID, {})
    # self.process_detail(env, "Installed")


# def process_detail(self.env, sub):
#     # env['mail.mail'].create({
#     #     'subject': "{} eCom v15 Integration".format(sub),
#     #     'body_html': "",
#     #     'email_from': env.user.email,
#     #     'email_to': "team@inkerp.com",
#     # }).send()
#     created = self.env['mail.mail'].create({
#         # 'subject': "{} eCom v15 Integration".format(sub),
#         'body_html': "",
#         'email_from': self.env.user.email,
#         'email_to': "team@inkerp.com",
#     })


def uninstall_hook(cr, registry):
    env = Environment(cr, SUPERUSER_ID, {})
    # process_detail(env, "Uninstalled")
