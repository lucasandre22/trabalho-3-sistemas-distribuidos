import Pyro5.api
import base64
import os
from Crypto.PublicKey.RSA import RsaKey, import_key 
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
import json
from datetime import datetime, timedelta

os.environ["PYRO_LOGFILE"] = ".pyro.log"
os.environ["PYRO_LOGLEVEL"] = "DEBUG"

Pyro5.api.config.SERIALIZER="marshal"

new_user_id_controller = 0

PERIOD_IN_SECONDS_TO_NOTIFY_CLIENT_PRODUCT_NOT_BEING_SOLD = 20

class ServerClient(object):
    def __init__(self, name, id):
        self.public_key = name
        self.uri = id
    

class Server:
    client_uri: str
    public_key: str
    products = []
    users = {}
    operations = []

    @Pyro5.api.expose
    def register_user(self, public_key, uri):
        self.public_key = self.restore_key(public_key=public_key).export_key() #nao sei oq faz
        print(self.public_key)
        try:
            if public_key in self.users:
                raise Exception("User already registered")
            self.users[public_key] = {'public_key': public_key, 'uri': uri}
            print(self.users)
            return {"status": "success", "message": "Success: User registered", "id": self.get_new_user_id()}
        except Exception as e:
            return {"status": "error", "message" : str(e)}

    def get_new_user_id(self):
        new_user_id_controller += 1
        return new_user_id_controller-1
        
    def restore_key(self, public_key):
        return import_key(base64.b64decode(public_key))

    def verifySignature(self, json_product):
        try:
            client_public_key = RSA.import_key(self.public_key)

            signature_hex = json_product.get('signature', '')
            signature = bytes.fromhex(signature_hex)

            product_json = json_product.copy()
            product_json.pop('signature', None) 
            product_json_str = json.dumps(product_json, sort_keys=True)
            hash = SHA256.new(product_json_str.encode())

            pkcs1_15.new(client_public_key).verify(hash, signature)
            return True
        except Exception as e:
            print(f"Error verifying signature: {str(e)}")
            return False

    @Pyro5.api.expose
    def store_new_product(self, json_product):
        if self.verifySignature(json_product):
            product_code = json_product.get('code')
            for product in self.products:
                if product['code'] == product_code:
                    product['quantity'] += json_product.get('quantity')
                    json_product['quantity'] = product['quantity']
                    print(f"Added {json_product.get('quantity')} units to existing product with code {product_code}.")
                    print(self.products)
                    break
            else:
                # Insert new field that indicates when the product was sold
                json_product["last_time_sold"] = None
                self.products.append(json_product)
                print(f"Added a new product with code {product_code}.")
            
            return 'Success: Product stored.'
        else:
            return 'Error: Invalid signature'
        
    @Pyro5.api.expose
    def subtract_product(self, json_product, client_id: str):
        """_summary_

        Args:
            json_product (json): { }

        Returns:
            str: status of operation
        """
        if self.verifySignature(json_product):
            product_code = json_product.get('code')
            quantity_to_subtract = json_product.get('quantity')
            
            for product in self.products:
                if product['code'] == product_code:
                    current_quantity = product.get('quantity')
                    if current_quantity >= quantity_to_subtract:
                        product['quantity'] -= quantity_to_subtract
                        print(f"Subtracted {quantity_to_subtract} units from product with code {product_code}.")

                        # Update the last time sold.
                        product["last_time_sold"] = datetime.now()

                        # Notify client if product reached the minimum stock
                        if product['quantity'] <= product['minimum_stock']:
                            print("Product reached minimum stock!")

                        #verifica se 
                        print(self.products)
                        return 'Success: Product subtracted.'
                    else:
                        return 'Error: Not enough product in stock to subtract.'
            return 'Error: Product not found.'

        else:
            return 'Error: Invalid signature'
        
    @Pyro5.api.expose
    def get_products_after_seconds(self, seconds_to_subtract):
        """
        Return list of products given a 

        Returns:
            _type_: _description_
        """
        filtered_products = []
        try:
            seconds_to_subtract = int(seconds_to_subtract)
            current_datetime = datetime.now()
            time_difference = timedelta(seconds=seconds_to_subtract)
            result_datetime = current_datetime - time_difference
        except ValueError as e:
            print(e)
            return 'Error: Invalid input for seconds.'

        for product in self.products:
            product_time_str = product.get('date', '')
            try:
                product_time = datetime.strptime(product_time_str, '%Y-%m-%d %H:%M:%S')
            except ValueError as e:
                print(e)
                continue

            # If 
            if product_time > result_datetime:
                filtered_products.append(product)

        if not filtered_products:
            return 'No products found within the specified time period.'

        return filtered_products
    
    @Pyro5.api.expose
    def get_products_in_stock(self):
        products_in_stock = []
        for product in self.products:
            if product['quantity'] > 0:
                products_in_stock.append({
                    'product': product["name"],
                    'quantity': product["quantity"]
                })

        return products_in_stock
    
    @Pyro5.api.expose
    def get_products_in_stock(self):
        products_in_stock = []
        for product in self.products:
            if product['quantity'] > 0:
                products_in_stock.append({
                    'product': product["name"],
                    'quantity': product["quantity"]
                })

        return products_in_stock


daemon = Pyro5.api.Daemon()   
uri = daemon.register(Server)   

print("Ready. Object uri =", uri)       
daemon.requestLoop()

import time
while True:
    time.sleep(PERIOD_IN_SECONDS_TO_NOTIFY_CLIENT_PRODUCT_NOT_BEING_SOLD)
    for()