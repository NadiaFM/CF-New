import logging
from odoo import models, fields, api
from odoo.exceptions import Warning, UserError
import base64
import requests
import time
try:
    import shopify
except ImportError:
    raise ImportError(
        'This module needs shopify library to connect with shopify. Please install ShopifyAPI on your system. (sudo pip3 install ShopifyAPI)')

_logger = logging.getLogger("=== Import Product Template ===")

class productproduct(models.Model):
    _inherit = "product.product"
    source_name=fields.Char('Product Source')
    shopify_instance_id=fields.Many2one('eg.ecom.instance','Shopify Instance')
        

class ProductTemplate(models.Model):
    _inherit = "product.template"
    source_name=fields.Char('Product Source')
    shopify_instance_id=fields.Many2one('eg.ecom.instance','Shopify Instance')
    def SyncInventory(self,instance_id):
        if not instance_id:
            return
        
        shop_connection = self.get_connection_from_shopify(instance_id=instance_id)
        if not shop_connection:
            return
        
        shopify_locations=shopify.Location.find()
        product_products= self.env["product.product"].search([('company_id','=',instance_id.company_id.id)])
    
        for product_product in product_products:
            eg_product_product=self.env["eg.product.product"].search([('odoo_product_id','=',product_product.id)])

            if not eg_product_product:
                continue
            shopify_id=eg_product_product[0].inst_product_id
            inventory_item_id=eg_product_product[0].inst_inventory_item_id
            inventory_level = shopify.InventoryLevel()
            quant=self.env['stock.quant'].search([('product_id','=',product_product.id),('quantity','>=',0),('location_id','=',instance_id.location_id.id)])
            if not quant:
                continue
            available_quantity=quant[0].available_quantity
            try:
                inventory_level.set(location_id=instance_id.shopify_location_id.location_id,inventory_item_id =inventory_item_id,available=int(available_quantity))
            except Exception as e:
                print(e)
                


    def import_product_from_shopify(self, instance_id=None, product_image=None, default_product_id=None):
        # raise UserError('here')
        status = "no"
        text = ""
        partial = False
        history_id_list = []
        products_without_sku=[]
        # created_product_count = 0  # Counter variable for created products

        if instance_id:
            shop_connection = self.get_connection_from_shopify(instance_id=instance_id)
            # raise UserError(str(default_product_id))

            if shop_connection:
                next_page_url = None
                count = 1
                while count > 0:
                    try:
                        if default_product_id:
                            response = shopify.Product.find(default_product_id)
                        else:
                            if next_page_url:
                                response = shopify.Product.find(from_=next_page_url) 
                            else:
                                response = shopify.Product.find(limit=5)

                    except Exception as e:
                        raise Warning("{}".format(e))

                    if response:
                        product_list = []
                        if default_product_id:
                            product_list.append(response)
                        else:
                            product_list = response
                        # raise UserError(product_list)

                        for product in product_list:
                            # if created_product_count >= 5:  # Check if 5 products are already created
                            #     break

                            product = product.to_dict()  # convert into dictionary
                            product_template_id = None
                            is_variant = True
                            eg_product_template_id = None
                            eg_product_tmpl_id = self.env["eg.product.template"].search(
                                [("inst_product_tmpl_id", "=", str(product.get("id"))),
                                ("instance_id", "=", instance_id.id), ("company_id", "=", instance_id.company_id.id)])
                            if (not eg_product_tmpl_id) or (
                                    eg_product_tmpl_id and (not eg_product_tmpl_id.odoo_product_tmpl_id)):
                                sku = product.get("variants")[0].get("barcode")
                                if not sku:
                                    products_without_sku.append({
                                    "id": product.get("id"),
                                    "name": product.get("title")
                                })
                                
                                    


                                    continue
                                # Asir - appending company with sku
                                product_id = self.env["product.product"].search(
                                    [("default_code", "=", sku), ("company_id.id", "=", instance_id.company_id.id)])
                                product_tmpl_id = None
                                eg_category_id = None
                                if not product_id:
                                    option = product.get("options")[0]
                                    # raise UserError(str(option))
                                    attribute_line_list = []

                                    # raise UserError("kuch bhi")
                                    if option.get("name") == "Title" and option.get("values")[0] == "Default Title":
                                        is_variant = False
                                        for product_variant in product.get("variants"):
                                    
                                    
                                            # Write weight unit
                                            uom_category_id = self.env["uom.category"].search([("name", "=", "Weight")],
                                                                                              limit=1)
                                            uom_id = self.env["uom.uom"].search(
                                                [("name", "in", ["kg", "KG"]),
                                                 ("category_id", "=", uom_category_id.id)], limit=1)
                                            inst_uom_id = self.env["uom.uom"].search(
                                                [("name", "=", product_variant.get("weight_unit")),
                                                 ("category_id", "=", uom_category_id.id)], limit=1)
                                            weight = round(
                                                inst_uom_id._compute_quantity(product_variant.get("weight"), uom_id), 2)
                                    
                                            product_tmpl_id = self.create([{"name": product.get("title"),
                                                                            "default_code": product_variant.get("barcode"),
                                                                            "type": "product",
                                                                            'source_name': "Shopifyy : " + instance_id.name,
                                                                            'shopify_instance_id': instance_id.id,
                                                                            'company_id': instance_id.company_id.id,
                                                                            "standard_price": product_variant.get(
                                                                                "compare_at_price") or 0,
                                                                            "list_price": product_variant.get("price"),
                                                                            # 'x_studio_shopify_id_1': "this",
                                    
                                                                            "weight": weight,
                                                                            }]
                                                                          )
                                            eg_product_template_id = self.env["eg.product.template"].create(
                                                {"inst_product_tmpl_id": str(product.get("id")),
                                                 "odoo_product_tmpl_id": product_tmpl_id.id,
                                                 "instance_id": instance_id.id,
                                                 "name": product_tmpl_id.name,
                                                 "price": product_tmpl_id.list_price,
                                                 "default_code": product_tmpl_id.default_code or "",
                                                 "weight": product_tmpl_id.weight,
                                                 "barcode": product_tmpl_id.barcode or "",
                                                 "update_required": False,
                                                 "company_id": instance_id.company_id.id,
                                                 "description": product.get("body_html"),
                                                 })
                                            product_tmpl_id.company_id=instance_id.company_id.id
                                    else:
                                        attribute_line_list = self.create_attribute_value_at_import(product=product,
                                                                                                instance_id=instance_id)

                                    if attribute_line_list:

                                        product_tmpl_id = self.create([{"name": product.get("title"),
                                                                        "type": "product",
                                                                        'source_name': "Shopify : " + instance_id.name,
                                                                        # 'x_studio_shopify_id_1':"that",

                                                                        'shopify_instance_id': instance_id.id,
                                                                        'company_id': instance_id.company_id.id,
                                                                        "attribute_line_ids": attribute_line_list[0]}])

                                        eg_product_template_id = self.env["eg.product.template"].create(
                                            {"inst_product_tmpl_id": str(product.get("id")),
                                            "odoo_product_tmpl_id": product_tmpl_id.id,
                                            "instance_id": instance_id.id,
                                            "name": product_tmpl_id.name,
                                            "price": product_tmpl_id.list_price,
                                            "default_code": product_tmpl_id.default_code or "",
                                            "weight": product_tmpl_id.weight,
                                            "barcode": product_tmpl_id.barcode or "",
                                            "company_id": instance_id.company_id.id,
                                            "update_required": False,
                                            "eg_attribute_line_ids": attribute_line_list[1],
                                            "description": product.get("body_html"),
                                            "eg_category_id": eg_category_id and eg_category_id.id or None,
                                            })
                                        product_tmpl_id.company_id = instance_id.company_id.id

                                else:
                                    product_tmpl_id = product_id.product_tmpl_id
                                    create_mapping = self.create_product_variant_at_import(product=product,
                                                                                        instance_id=instance_id,
                                                                                        product_tmpl_id=product_tmpl_id,
                                                                                        check_attribute=True)
                                    if create_mapping:
                                        attribute_line_list = self.create_attribute_value_at_import(product=product,
                                                                                                    instance_id=instance_id,
                                                                                                    product_tmpl_id=product_tmpl_id)

                                        eg_product_template_id = self.env["eg.product.template"].create(
                                            {"inst_product_tmpl_id": str(product.get("id")),
                                            "odoo_product_tmpl_id": product_tmpl_id.id,
                                            "instance_id": instance_id.id,
                                            "name": product_tmpl_id.name,
                                            "price": product_tmpl_id.list_price,
                                            "default_code": product_tmpl_id.default_code or "",
                                            "weight": product_tmpl_id.weight,
                                            "barcode": product_tmpl_id.barcode or "",
                                            "company_id": instance_id.company_id.id,
                                            "update_required": False,
                                            "eg_attribute_line_ids": attribute_line_list[1],
                                            "description": product.get("body_html"),
                                            "eg_category_id": eg_category_id and eg_category_id.id or None
                                            })
                                        product_tmpl_id.company_id = instance_id.company_id.id
                                        create_variant = self.create_product_variant_at_import(product=product,
                                                                                            instance_id=instance_id,
                                                                                            product_tmpl_id=product_tmpl_id,
                                                                                            eg_product_template_id=eg_product_template_id,
                                                                                            check_attribute_create_mapping=True,
                                                                                            eg_category_id=eg_category_id)
                                        status = "yes"
                                        text = "This product was successfully created and mapped"
                                        product_template_id = product_tmpl_id
                                        # created_product_count += 1  # Increment the created product count
                                    else:
                                        text = "This odoo product {} is  not same attribute and value for shopify product so it is not mapping".format(
                                            product_id.name)
                                        partial = True
                                        product_template_id = product_tmpl_id
                                        status = "no"
                                        _logger.info(
                                            "This odoo product {} is  not same attribute and value for shopify product so it is not mapping".format(
                                                product_id.name))
                                if not product_id:
                                    if eg_product_template_id:
                                        create_variant = self.create_product_variant_at_import(product=product,
                                                                                            instance_id=instance_id,
                                                                                            product_tmpl_id=product_tmpl_id,
                                                                                            eg_product_template_id=eg_product_template_id,
                                                                                            eg_category_id=eg_category_id)

                                        status = "yes"
                                        text = "This product was successfully created and mapped"
                                        product_template_id = product_tmpl_id
                                        # created_product_count += 1  # Increment the created product count
                                    else:
                                        partial = True
                                        status = "no"
                                        text = "This product is not created and not mapped"
                            else:
                                eg_new_product_tmpl_id = self.create_remaining_product_variant_import(
                                    eg_product_tmpl_id=eg_product_tmpl_id, product=product, instance_id=instance_id)

                                text = "This product is already mapped but so update variant"
                                status = "yes"
                                product_template_id = eg_product_tmpl_id.odoo_product_tmpl_id
                            eg_history_id = self.env["eg.sync.history"].create({"error_message": text,
                                                                                "status": status,
                                                                                "process_on": "product",
                                                                                "process": "a",
                                                                                "instance_id": instance_id.id,
                                                                                "product_id": product_template_id and product_template_id.id or None,
                                                                                "child_id": True})
                            history_id_list.append(eg_history_id.id)
                        # raise UserError(products_without_sku)
                        time.sleep(1) 
                        if default_product_id:
                            break
                        else:
                            next_page_url = response.next_page_url
                            if not next_page_url:
                                break
                    else:
                        text = "Not get response"
                        break
            else:
                text = "Not Connect to store !!!"
        else:
            text = "Not Found Instance !!!"
        if partial:
            status = "partial"
            text = "Some product was created and some product is not create"
        if status == "yes" and not partial:
            text = "All product was successfully created and mapped"
        eg_history_id = self.env["eg.sync.history"].create({"error_message": text,
                                                            "status": status,
                                                            "process_on": "product",
                                                            "process": "a",
                                                            "instance_id": instance_id and instance_id.id or None,
                                                            "parent_id": True,
                                                            "eg_history_ids": [(6, 0, history_id_list)]})
        return True


    def get_connection_from_shopify(self, instance_id=None):
        shop_url = "https://{}:{}@{}.myshopify.com/admin/api/{}".format(instance_id.shopify_api_key,
                                                                        instance_id.shopify_password,
                                                                        instance_id.shopify_shop,
                                                                        instance_id.shopify_version)
        try:
            shopify.ShopifyResource.set_site(shop_url)
            connection = True
        except Exception as e:
            _logger.info("{}".format(e))
            connection = False
        return connection

    def create_remaining_product_variant_import(self, eg_product_tmpl_id=None, product=None, instance_id=None):
        if eg_product_tmpl_id and product:
            option = product.get("options")[0]
            if option.get("name") == "Title" and option.get("values")[0] == "Default Title":
                return True
            variant_mapping = False
            new_option_list = []
            product_tmpl_id = eg_product_tmpl_id.odoo_product_tmpl_id
            for option in product.get("options"):
                value_list = []
                eg_value_list = []
                attribute_id = self.env["product.attribute"].search([("name", "=", option.get("name"))])
                attribute_line_id = None
                eg_product_attribute_id = self.env["eg.product.attribute"].search(
                    [("name", "=", option.get("name")), ("instance_id", "=", instance_id.id)])
                if attribute_id:
                    if not eg_product_attribute_id:
                        eg_product_attribute_id = self.env["eg.product.attribute"].create(
                            {"odoo_attribute_id": attribute_id.id,
                             "instance_id": instance_id.id,
                             "inst_attribute_id": str(option.get("id"))})

                    attribute_line_id = product_tmpl_id.attribute_line_ids.filtered(
                        lambda l: l.attribute_id == attribute_id)

                    if attribute_line_id:
                        for value in option.get("values"):
                            value_id = self.env["product.attribute.value"].search(
                                [("name", "=", value), ("attribute_id", "=", attribute_id.id)])
                            eg_value_id = self.env["eg.attribute.value"].search(
                                [("odoo_attribute_id", "=", attribute_id.id),
                                 ("name", "=", value), ("instance_id", "=", instance_id.id)])
                            if value_id:
                                if not eg_value_id:
                                    eg_value_id = self.env["eg.attribute.value"].create(
                                        {"odoo_attribute_value_id": value_id.id,
                                         "inst_attribute_id": eg_product_attribute_id.id,
                                         "instance_id": instance_id.id,
                                         "odoo_attribute_id": attribute_id.id,
                                         })
                                for attribute_line in product_tmpl_id.attribute_line_ids:
                                    if attribute_line.attribute_id == attribute_id and attribute_line.value_ids and value_id not in attribute_line.value_ids:
                                        value_list.append(value_id.id)
                                        eg_value_list.append(eg_value_id.id)
                            else:
                                value_id = self.env["product.attribute.value"].create({"attribute_id": attribute_id.id,
                                                                                       "name": value})
                                eg_value_id = self.env["eg.attribute.value"].create(
                                    {"odoo_attribute_value_id": value_id.id,
                                     "inst_attribute_id": eg_product_attribute_id.id,
                                     "instance_id": instance_id.id,
                                     "odoo_attribute_id": attribute_id.id,
                                     })
                                value_list.append(value_id.id)
                                eg_value_list.append(eg_value_id.id)
                        if value_list and eg_value_list:
                            attribute_line_id = self.env["product.template.attribute.line"].search(
                                [("product_tmpl_id", "=", product_tmpl_id.id), ("attribute_id", "=", attribute_id.id),
                                 ("value_ids", "!=", None)])
                            eg_attribute_line_id = self.env["eg.product.attribute.line"].search(
                                [("eg_product_tmpl_id", "=", eg_product_tmpl_id.id),
                                 ("eg_product_attribute_id", "=", eg_product_attribute_id.id),
                                 ("eg_value_ids", "!=", None)])
                            if attribute_line_id:
                                for value_id in value_list:
                                    attribute_line_id.write({"value_ids": [(4, value_id, 0)]})  # Start this code
                                product_tmpl_id._create_variant_ids()
                            if eg_attribute_line_id:
                                for eg_value_id in eg_value_list:
                                    eg_attribute_line_id.write({"eg_value_ids": [(4, eg_value_id, 0)]})
                                variant_mapping = True
                if not attribute_id or not attribute_line_id:
                    new_option_list.append(option.get("name"))
            if variant_mapping:
                new_variant_mapping = self.create_product_variant_at_import(instance_id=instance_id, product=product,
                                                                            product_tmpl_id=product_tmpl_id,
                                                                            eg_product_template_id=eg_product_tmpl_id,
                                                                            new_option_list=new_option_list)
                return True
            else:
                return False

    def create_attribute_value_at_import(self, product=None, instance_id=None,
                                         product_tmpl_id=None):  # new code for v13
        attribute_line_list = []
        eg_attribute_line_list = []
        for option in product.get("options"):
            if option.get("name") == "Title" and option.get("values")[0] == "Default Title":
                continue
            if product_tmpl_id:
                attribute_line_id = product_tmpl_id.attribute_line_ids.filtered(  # new code for v13
                    lambda l: l.attribute_id.name == option.get("name"))
                if not attribute_line_id:
                    continue
            eg_product_attribute_id = self.env["eg.product.attribute"].search(
                [("name", "=", option.get("name")), ("instance_id", "=", instance_id.id)])
            value_list = []
            eg_value_list = []
            if not eg_product_attribute_id:
                product_attribute_id = self.env["product.attribute"].search(
                    [("name", "=", option.get("name"))])
                if not product_attribute_id:
                    product_attribute_id = self.env[
                        "product.attribute"].create({"name": option.get("name")})
                    eg_product_attribute_id = self.env["eg.product.attribute"].create(
                        {"odoo_attribute_id": product_attribute_id.id,
                         "instance_id": instance_id.id,
                         "inst_attribute_id": str(option.get("id"))})
                    for value in option.get("values"):
                        attribute_value_id = self.env["product.attribute.value"].create(
                            {"attribute_id": product_attribute_id.id,
                             "name": value})
                        eg_attribute_value_id = self.env["eg.attribute.value"].create(
                            {"odoo_attribute_value_id": attribute_value_id.id,
                             "inst_attribute_id": eg_product_attribute_id.id,
                             "instance_id": instance_id.id,
                             "odoo_attribute_id": product_attribute_id.id,
                             })
                        value_list.append(attribute_value_id.id)
                        eg_value_list.append(eg_attribute_value_id.id)
                    attribute_line_list.append((0, 0, {"attribute_id": product_attribute_id.id,
                                                       "value_ids": [(6, 0, value_list)]}))
                    eg_attribute_line_list.append((0, 0, {"eg_product_attribute_id": eg_product_attribute_id.id,
                                                          "eg_value_ids": [(6, 0, eg_value_list)]}))

                else:
                    eg_product_attribute_id = self.env["eg.product.attribute"].create(
                        {"odoo_attribute_id": product_attribute_id.id,
                         "instance_id": instance_id.id,
                         "inst_attribute_id": str(option.get("id"))})
                    for value in option.get("values"):
                        attribute_value_id = self.env["product.attribute.value"].search(
                            [("name", "=", value), ("attribute_id", "=", product_attribute_id.id)])
                        if not attribute_value_id:
                            attribute_value_id = self.env["product.attribute.value"].create(
                                {"attribute_id": product_attribute_id.id,
                                 "name": value})

                            eg_attribute_value_id = self.env["eg.attribute.value"].create(
                                {"odoo_attribute_value_id": attribute_value_id.id,
                                 "inst_attribute_id": eg_product_attribute_id.id,
                                 "instance_id": instance_id.id,
                                 "odoo_attribute_id": product_attribute_id.id,
                                 })
                        else:
                            eg_attribute_value_id = self.env["eg.attribute.value"].search(
                                [("odoo_attribute_value_id", "=", attribute_value_id.id),
                                 ("instance_id", "=", instance_id.id),
                                 ("odoo_attribute_id", "=", product_attribute_id.id)])
                            if not eg_attribute_value_id:
                                eg_attribute_value_id = self.env["eg.attribute.value"].create(
                                    {"odoo_attribute_value_id": attribute_value_id.id,
                                     "inst_attribute_id": eg_product_attribute_id.id,
                                     "instance_id": instance_id.id,
                                     "odoo_attribute_id": product_attribute_id.id,
                                     })
                        value_list.append(attribute_value_id.id)
                        eg_value_list.append(eg_attribute_value_id.id)
                    attribute_line_list.append((0, 0, {"attribute_id": product_attribute_id.id,
                                                       "value_ids": [(6, 0, value_list)]}))
                    eg_attribute_line_list.append((0, 0, {"eg_product_attribute_id": eg_product_attribute_id.id,
                                                          "eg_value_ids": [(6, 0, eg_value_list)]}))

            else:
                product_attribute_id = eg_product_attribute_id.odoo_attribute_id
                for value in option.get("values"):
                    eg_attribute_value_id = self.env["eg.attribute.value"].search(
                        [("odoo_attribute_id", "=", product_attribute_id.id),
                         ("name", "=", value), ("instance_id", "=", instance_id.id)])
                    if not eg_attribute_value_id:
                        attribute_value_id = self.env["product.attribute.value"].search(
                            [("name", "=", value), ("attribute_id", "=", product_attribute_id.id)])
                        if not attribute_value_id:
                            attribute_value_id = self.env["product.attribute.value"].create(
                                {"attribute_id": product_attribute_id.id,
                                 "name": value})
                            eg_attribute_value_id = self.env["eg.attribute.value"].create(
                                {"odoo_attribute_value_id": attribute_value_id.id,
                                 "inst_attribute_id": eg_product_attribute_id.id,
                                 "instance_id": instance_id.id,
                                 "odoo_attribute_id": product_attribute_id.id,
                                 })
                        else:
                            eg_attribute_value_id = self.env["eg.attribute.value"].create(
                                {"odoo_attribute_value_id": attribute_value_id.id,
                                 "inst_attribute_id": eg_product_attribute_id.id,
                                 "instance_id": instance_id.id,
                                 "odoo_attribute_id": product_attribute_id.id,
                                 })
                    else:
                        attribute_value_id = eg_attribute_value_id.odoo_attribute_value_id

                    value_list.append(attribute_value_id.id)
                    eg_value_list.append(eg_attribute_value_id.id)
                attribute_line_list.append((0, 0, {"attribute_id": product_attribute_id.id,
                                                   "value_ids": [(6, 0, value_list)]}))
                eg_attribute_line_list.append((0, 0, {"eg_product_attribute_id": eg_product_attribute_id.id,
                                                      "eg_value_ids": [(6, 0, eg_value_list)]}))

        return [attribute_line_list, eg_attribute_line_list]

    def create_product_variant_at_import(self, product=None, instance_id=None, product_tmpl_id=None,
                                         eg_product_template_id=None, check_attribute=None, new_option_list=None,
                                         eg_category_id=None, check_attribute_create_mapping=None):
        same_attribute = True
        temp_image_url = None
        for image in product.get("images",[]):
            temp_image_url=image.get("src",'')
            if product_tmpl_id:
                product_tmpl_id.image_1920 = base64.b64encode(requests.get(temp_image_url.strip()).content).replace(b"\n", b"")
            if eg_product_template_id:
                eg_product_template_id.product_tmpl_image=base64.b64encode(requests.get(temp_image_url.strip()).content).replace(b"\n", b"")
                    
        for product_variant in product.get("variants"):
            image_url=""
            for image in product.get("images",[]):
                if product_variant.get('id','') in image.get('variant_ids',[]):
                    image_url=image.get("src",'')
                    if image_url!='':
                        break
            if image_url=="" and temp_image_url:
                image_url=temp_image_url

            # value_list = []
            eg_product_id = None
            if not check_attribute:
                eg_product_id = self.env["eg.product.product"].search(
                    [("inst_product_id", "=", str(product_variant.get("id"))),
                     ("eg_tmpl_id", "=", eg_product_template_id.id)])
            if not eg_product_id:
                attribute_value_ids = self.env["product.template.attribute.value"]

                for count in range(len(product.get("options"))):
                    attribute_name = product.get("options")[count].get("name")
                    attribute_line_id = None
                    if product_tmpl_id.attribute_line_ids:
                        attribute_line_id = product_tmpl_id.attribute_line_ids.filtered(  # new code for v13
                            lambda l: l.attribute_id.name == attribute_name)
                    if new_option_list:
                        if attribute_name in new_option_list:
                            continue
                    if check_attribute or check_attribute_create_mapping:
                        if product_tmpl_id.attribute_line_ids:
                            attribute_list = product_tmpl_id.attribute_line_ids.mapped("attribute_id.name")
                            if attribute_name not in attribute_list:
                                continue
                    option = "option" + str(count + 1)
                    if product_variant.get(option):
                        condition_list = [("name", "=", product_variant.get(option)),  # new code for v13
                                          ("attribute_id.name", "=", attribute_name)]
                        if attribute_line_id:
                            condition_list.append(("attribute_line_id", "=", attribute_line_id.id))
                        attribute_value_ids += self.env["product.template.attribute.value"].search(condition_list)
                product_id = product_tmpl_id.product_variant_ids.filtered(  # TODO for remove new attribute value
                    lambda l: l.product_template_attribute_value_ids == attribute_value_ids)
                if product_id:
                    if check_attribute:
                        continue
                    uom_category_id = self.env["uom.category"].search([("name", "=", "Weight")],
                                                                      limit=1)
                    uom_id = self.env["uom.uom"].search(
                        [("name", "in", ["kg", "KG"]), ("category_id", "=", uom_category_id.id)], limit=1)
                    inst_uom_id = self.env["uom.uom"].search(
                        [("name", "=", product_variant.get("weight_unit")),
                         ("category_id", "=", uom_category_id.id)], limit=1)
                    weight = round(inst_uom_id._compute_quantity(product_variant.get("weight"), uom_id), 2)
                    price=product_variant.get("price")
                    try:
                        price=float(price)
                    except:
                        price=0
                    standardprice=product_variant.get("compare_at_price")
                    try:
                        standardprice=float(standardprice)
                    except:
                        standardprice=0

                    product_id.write({"default_code": product_variant.get("barcode"),
                                      "standard_price": standardprice,
                                      "lst_price": price,
                                    #   "barcode": product_variant.get("barcode") or None,
                                      "weight": weight,
                                      'source_name':"Shopify : "+instance_id.name,
                                      'shopify_instance_id':instance_id.id,
                                      'company_id':instance_id.company_id.id
                                      })
                    eg_value_ids = self.env["eg.attribute.value"].search(
                        [("odoo_attribute_value_id", "in",
                          product_id.product_template_attribute_value_ids.mapped("product_attribute_value_id.id")),
                         ("instance_id", "=", instance_id.id)])
                    product_var_id = self.env["eg.product.product"].create({"odoo_product_id": product_id.id,
                                                           "instance_id": instance_id.id,
                                                           "inst_product_id": str(product_variant.get("id")),
                                                           "eg_tmpl_id": eg_product_template_id.id,
                                                           "inst_inventory_item_id": str(
                                                               product_variant.get("inventory_item_id")),
                                                           "name": product_id.name,
                                                           "price": product_id.lst_price,
                                                           "default_code": product_id.default_code or "",
                                                           "weight": product_id.weight,
                                                           "barcode": product_id.barcode or "",
                                                           "company_id": instance_id.company_id.id,
                                                           "update_required": False,
                                                           "eg_value_ids": [(6, 0, eg_value_ids.ids)],
                                                           "eg_category_id": eg_category_id and eg_category_id.id or None,
                                                           })
                    if image_url!='':
                        product_var_id.product_image=base64.b64encode(requests.get(image_url.strip()).content).replace(b"\n", b"")
                        product_var_id.odoo_product_id.image_1920 = base64.b64encode(requests.get(image_url.strip()).content).replace(b"\n", b"")
                    #Asir - on default location Block 10 Street 100 House 46 = 18459557937
                    if instance_id.sync_inventory_to_shopify:
                        try:
                            inventory_level = shopify.InventoryLevel()
                            locations = shopify.Location.find()
                            inventory_level.set(location_id = instance_id.shopify_location_id.location_id, inventory_item_id = product_var_id.inst_inventory_item_id, available = 0)
                        except:
                            pass
                        #Asir - set stock.quant line
                        stock_quant_rec = self.env['stock.quant'].create({
                            'location_id': instance_id.location_id.id,
                            'product_id': product_var_id.odoo_product_id.id,
                            'quantity': 0,
                        })
                        stock_quant_rec.action_apply_inventory()
                else:
                    same_attribute = False

        return same_attribute

    def export_product_in_middle_layer(self, instance_id=None, product_detail=None, product_image=None):
        product_tmpl_ids = self.browse(self._context.get("active_ids"))
        if product_tmpl_ids:
            product_tmpl_ids = product_tmpl_ids.filtered(lambda l: l.type == "product")
        else:
            product_tmpl_ids = self.search([("type", "=", "product")])
        # raise UserError(product_tmpl_ids)
        if product_detail:
            for product_tmpl_id in product_tmpl_ids:
                if product_tmpl_id.product_variant_ids:
                    continue_product = False
                    for product_variant in product_tmpl_id.product_variant_ids:
                        if not product_variant.default_code:
                            continue_product = True
                    if continue_product:
                        continue
                else:
                    if not product_tmpl_id.default_code:
                        continue
                eg_product_tmpl_id = self.env["eg.product.template"].search(
                    [("odoo_product_tmpl_id", "=", product_tmpl_id.id), ("instance_id", "=", instance_id.id)])
                eg_category_id = None
                if not eg_product_tmpl_id:
                    eg_product_tmpl_id = self.env["eg.product.template"].create(
                        {
                            "odoo_product_tmpl_id": product_tmpl_id.id,
                            "instance_id": instance_id.id,
                            "name": product_tmpl_id.name,
                            "price": product_tmpl_id.list_price,
                            "default_code": product_tmpl_id.default_code or "",
                            "weight": product_tmpl_id.weight,
                            "barcode": product_tmpl_id.barcode or "",
                            "update_required": True,
                            "eg_category_id": eg_category_id and eg_category_id.id or None
                        })
                    if product_tmpl_id.attribute_line_ids:
                        attribute_line_list = []
                        for attribute_line_id in product_tmpl_id.attribute_line_ids:
                            eg_attribute_id = self.env["eg.product.attribute"].search(
                                [("odoo_attribute_id", "=", attribute_line_id.attribute_id.id),
                                 ("instance_id", "=", instance_id.id)])
                            value_list = []
                            if not eg_attribute_id:
                                eg_attribute_id = self.env["eg.product.attribute"].create(
                                    {"odoo_attribute_id": attribute_line_id.attribute_id.id,
                                     "instance_id": instance_id.id})
                                for value_id in attribute_line_id.value_ids:
                                    eg_value_id = self.env["eg.attribute.value"].search(
                                        [("inst_attribute_id", "=", eg_attribute_id.id),
                                         ("instance_id", "=", instance_id.id),
                                         ("odoo_attribute_value_id", "=", value_id.id)])
                                    if not eg_value_id:
                                        eg_value_id = self.env["eg.attribute.value"].create(
                                            {"odoo_attribute_value_id": value_id.id,
                                             "inst_attribute_id": eg_attribute_id.id,
                                             "instance_id": instance_id.id,
                                             "odoo_attribute_id": attribute_line_id.attribute_id.id, })
                                    value_list.append(eg_value_id.id)
                                attribute_line_list.append((0, 0, {"eg_product_attribute_id": eg_attribute_id.id,
                                                                   "eg_value_ids": [(6, 0, value_list)]}))
                            else:
                                for value_id in attribute_line_id.value_ids:
                                    eg_value_id = self.env["eg.attribute.value"].search(
                                        [("inst_attribute_id", "=", eg_attribute_id.id),
                                         ("instance_id", "=", instance_id.id),
                                         ("odoo_attribute_value_id", "=", value_id.id)])
                                    if not eg_value_id:
                                        eg_value_id = self.env["eg.attribute.value"].create(
                                            {"odoo_attribute_value_id": value_id.id,
                                             "inst_attribute_id": eg_attribute_id.id,
                                             "instance_id": instance_id.id,
                                             "odoo_attribute_id": attribute_line_id.attribute_id.id, })
                                    value_list.append(eg_value_id.id)
                                attribute_line_list.append((0, 0, {"eg_product_attribute_id": eg_attribute_id.id,
                                                                   "eg_value_ids": [(6, 0, value_list)]}))

                        eg_product_tmpl_id.write({"eg_attribute_line_ids": attribute_line_list})
                    # raise UserError("i")
                    eg_product_ids = self.export_product_variant_in_middle_layer(instance_id=instance_id,
                                                                                 eg_product_tmpl_id=eg_product_tmpl_id,
                                                                                 product_tmpl_id=product_tmpl_id,
                                                                                 eg_category_id=eg_category_id)
                else:
                    # raise UserError("sdg")
                    eg_product_tmpl_id = self.export_update_product_in_middle_layer(
                        eg_product_tmpl_id=eg_product_tmpl_id)

    def export_product_variant_in_middle_layer(self, instance_id=None, eg_product_tmpl_id=None, product_tmpl_id=None,
                                               eg_category_id=None):
        if product_tmpl_id.product_variant_ids:
            for product_variant_id in product_tmpl_id.product_variant_ids:
                eg_value_ids = self.env["eg.attribute.value"].search(
                    [("odoo_attribute_value_id", "in",
                      product_variant_id.product_template_attribute_value_ids.mapped("product_attribute_value_id.id")),
                     ("instance_id", "=", instance_id.id)])
                eg_product_id = self.env["eg.product.product"].create({"odoo_product_id": product_variant_id.id,
                                                                       "instance_id": instance_id.id,
                                                                       "eg_tmpl_id": eg_product_tmpl_id.id,
                                                                       "name": product_variant_id.name,
                                                                       "price": product_variant_id.lst_price,
                                                                       "default_code": product_variant_id.default_code or "",
                                                                       "weight": product_variant_id.weight,
                                                                       "barcode": product_variant_id.barcode or "",
                                                                       "company_id": instance_id.company_id.id,
                                                                       "eg_value_ids": [(6, 0, eg_value_ids.ids)],
                                                                       "update_required": True,
                                                                       "eg_category_id": eg_category_id and eg_category_id.id or None
                                                                       })
            return True

    def export_product_in_shopify(self, instance_id=None):
        status = "no"
        text = ""
        partial = False
        history_id_list = []
        eg_product_tmpl_ids = self.env["eg.product.template"].browse(self._context.get("active_ids"))
        if not eg_product_tmpl_ids:
            eg_product_tmpl_ids = self.env["eg.product.template"].search([("instance_id", "=", instance_id.id)])
        
        if eg_product_tmpl_ids:
            
            eg_product_tmpl_ids = eg_product_tmpl_ids.filtered(lambda l: not l.inst_product_tmpl_id)
            for eg_product_tmpl_id in eg_product_tmpl_ids:
                status = "no"
                instance_id = eg_product_tmpl_id.instance_id
                shop_connection = self.get_connection_from_shopify(instance_id=instance_id)
                if shop_connection:
                    vendor = eg_product_tmpl_id.odoo_product_tmpl_id.seller_ids and \
                             eg_product_tmpl_id.odoo_product_tmpl_id.seller_ids[0].name.name or ""

                    product = {"title": eg_product_tmpl_id.name or "",
                               "vendor": vendor,
                               "product_type": eg_product_tmpl_id.eg_category_id and eg_product_tmpl_id.eg_category_id.name or ""
                               }
                    variants = []
                    options = []
                    if eg_product_tmpl_id.eg_attribute_line_ids:
                        for eg_attribute_line_id in eg_product_tmpl_id.eg_attribute_line_ids:
                            options.append({"name": eg_attribute_line_id.eg_product_attribute_id.name,
                                            "values": eg_attribute_line_id.eg_value_ids.mapped("name")})
                        for eg_product_id in eg_product_tmpl_id.eg_product_ids:
                            # Below update code for not change attribute value
                            option = []
                            for eg_attribute_line_id in eg_product_tmpl_id.eg_attribute_line_ids:
                                value_id = eg_product_id.eg_value_ids.filtered(
                                    lambda l: l.inst_attribute_id == eg_attribute_line_id.eg_product_attribute_id)
                                option.append(value_id.name)
                            option_count = len(option)
                            variants.append({"option1": option[0],
                                             "option2": option_count in [2, 3] and option[1] or "",
                                             "option3": option_count == 3 and option[2] or "",
                                             "price": str(eg_product_id.price),
                                             "sku": eg_product_id.default_code or "",
                                             "weight": str(eg_product_id.weight),
                                             "weight_unit": "kg",
                                             "barcode": eg_product_id.barcode or ""
                                             })

                    else:
                        variants.append({"option1": "Default Title",
                                         "price": str(eg_product_tmpl_id.price),
                                         "sku": eg_product_tmpl_id.default_code or "",
                                         "weight": str(eg_product_tmpl_id.weight),
                                         "weight_unit": "kg",
                                         "barcode": eg_product_tmpl_id.barcode or ""
                                         })
                    product.update({"variants": variants,
                                    "options": options})
                    response = None
                    try:
                        response = shopify.Product.create(product)
                    except Exception as e:
                        text = "This {} product is not export and error is {}".format(eg_product_tmpl_id.name, e)
                        partial = True
                        # error = True
                        _logger.info("This {} product is not export and error is {}".format(eg_product_tmpl_id.name, e))
                    if response and response.id:
                        response = response.to_dict()
                        product_mapping = self.export_product_mapping(response=response,
                                                                      eg_product_tmpl_id=eg_product_tmpl_id,
                                                                      instance_id=instance_id)
                        status = "yes"
                        text = "This product is successfully export in shopify "
                    elif response:
                        text = "{}".format(response.errors.errors)
                        partial = True

                    eg_history_id = self.env["eg.sync.history"].create({"error_message": text,
                                                                        "status": status,
                                                                        "process_on": "product",
                                                                        "process": "b",
                                                                        "instance_id": instance_id.id,
                                                                        "product_id": eg_product_tmpl_id.odoo_product_tmpl_id.id,
                                                                        "child_id": True})
                    history_id_list.append(eg_history_id.id)
                else:
                    text = "Not Connect to store !!!"
            if partial:
                status = "partial"
                text = "Some product was exported and some product is not exported"
            if status == "yes" and not partial:
                text = "All product was successfully exported in shopify"
            eg_history_id = self.env["eg.sync.history"].create({"error_message": text,
                                                                "status": status,
                                                                "process_on": "product",
                                                                "process": "b",
                                                                "instance_id": instance_id and instance_id.id or None,
                                                                "parent_id": True,
                                                                "eg_history_ids": [(6, 0, history_id_list)]})

    def export_product_mapping(self, response=None, eg_product_tmpl_id=None, instance_id=None):
        if response and eg_product_tmpl_id:
            product = response
            eg_product_tmpl_id.write({"inst_product_tmpl_id": str(product.get("id")),
                                      "update_required": False})
            attribute_list = []
            for option in product.get("options"):
                attribute_list.append(option.get("name"))
            for product_variant in product.get("variants"):
                value_list = []
                for option in ["option1", "option2", "option3"]:
                    if product_variant.get(option):
                        value_list.append(product_variant.get(option))
                eg_value_ids = self.env["eg.attribute.value"].search(
                    [("name", "in", value_list), ("instance_id", "=", instance_id.id),
                     ("inst_attribute_id.name", "=", attribute_list)])
                for eg_product_id in eg_product_tmpl_id.eg_product_ids:
                    if eg_product_id.eg_value_ids == eg_value_ids:
                        eg_product_id.write({"inst_product_id": str(product_variant.get("id")),
                                             "update_required": False,
                                             "inst_inventory_item_id": str(
                                                 product_variant.get("inventory_item_id"))})
                        break
        return True

    def export_update_product_in_middle_layer(self, instance_id=None, eg_product_tmpl_id=None):
        if eg_product_tmpl_id:
            product_tmpl_id = eg_product_tmpl_id.odoo_product_tmpl_id
            eg_product_tmpl_id.write({"name": product_tmpl_id.name,
                                      "price": product_tmpl_id.list_price,
                                      "default_code": product_tmpl_id.default_code or "",
                                      "weight": product_tmpl_id.weight,
                                      "barcode": product_tmpl_id.barcode or "",
                                      "qty_available": int(product_tmpl_id.qty_available),
                                      "update_required": True, })
            for eg_product_id in eg_product_tmpl_id.eg_product_ids:
                product_id = eg_product_id.odoo_product_id
                eg_product_id.write({"name": product_id.name,
                                     "price": product_id.lst_price,
                                     "default_code": product_id.default_code or "",
                                     "weight": product_id.weight,
                                     "barcode": product_id.barcode or "",
                                     "qty_available": int(product_id.qty_available),
                                     "update_required": True, })
            return True
