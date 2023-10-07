import Pyro5.api
import base64
import os
from Crypto.PublicKey.RSA import RsaKey, import_key 
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
import json

os.environ["PYRO_LOGFILE"] = ".pyro.log"
os.environ["PYRO_LOGLEVEL"] = "DEBUG"

Pyro5.api.config.SERIALIZER="marshal"

class Server:
    client_uri: str
    public_key: str
    products = []
    users = {}
    operations = []

    @Pyro5.api.expose
    def register(self, public_key, uri):
        self.public_key = self.restore_key(public_key=public_key).export_key() #nao sei oq faz
        try:
            if public_key in self.users:
                return 'Error: User already registered.'
            self.users[public_key] = {'public_key': public_key, 'uri': uri}
            print(self.users)
            return 'Success: User registered.'
        except Exception as e:
            return f'Error registering user: {str(e)}'


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
                    self.products.append(json_product)
                    print(f"Added {json_product.get('quantity')} units to existing product with code {product_code}.")
                    print(self.products)
                    break
            else:
                self.products.append(json_product)
                print(f"Added a new product with code {product_code}.")
                return 'Success: Product stored.'
        else:
            return 'Error: Invalid signature'
        
    @Pyro5.api.expose
    def subtract_product(self, json_product):
        if self.verifySignature(json_product):
            product_code = json_product.get('code')
            quantity_to_subtract = json_product.get('quantity')
            
            for product in self.products:
                if product['code'] == product_code:
                    current_quantity = product.get('quantity')
                    if current_quantity >= quantity_to_subtract:
                        product['quantity'] -= quantity_to_subtract
                        print(f"Subtracted {quantity_to_subtract} units from product with code {product_code}.")
                        print(self.products)
                        return 'Success: Product subtracted.'
                    else:
                        return 'Error: Not enough stock to subtract.'
            return 'Error: Product not found.'

        else:
            return 'Error: Invalid signature'
        


daemon = Pyro5.api.Daemon()   
uri = daemon.register(Server)   

print("Ready. Object uri =", uri)       
daemon.requestLoop()