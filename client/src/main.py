import Pyro5.api
import os
import base64
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from dotenv import load_dotenv
import datetime

load_dotenv() 

os.environ["PYRO_LOGFILE"] = "pyro.log"
os.environ["PYRO_LOGLEVEL"] = "INFO"

Pyro5.api.config.SERIALIZER="marshal"

def read_user_from_input():
    name = input("Enter your name: ")
    public_key = input("Enter your public key: ")
    remote_uri = input("Enter the remote URI: ")

    return {'name': name, 'public_key': public_key, 'remote_uri': remote_uri}

def read_product_from_input():
    code = input("Enter the product code: ")
    name = input("Enter the product name: ")
    description = input("Enter the product description: ")
    quantity = int(input("Enter the product quantity: "))
    unit_price = float(input("Enter the product unit price: "))
    minimum_stock = int(input("Enter the product minimum stock: "))

    current_datetime = datetime.datetime.now()
    formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
    
    product = {
        'code': code,
        'name': name,
        'description': description,
        'quantity': quantity,
        'unit_price': unit_price,
        'minimum_stock': minimum_stock,
        'date': formatted_datetime
    }

    return product

def sendNewProduct(server, json_product):
    # assina json_product antes
    response = server.store_new_product(json_product)
    return response

class Client(object):

    @Pyro5.api.expose
    def notifyProductEmptying(self):
        print("")

    @Pyro5.api.expose
    def notifyProductNotBeingSold(self):
        print("")
    
message = b'To be signed'

hash = SHA256.new(message)
private_key = RSA.import_key(open(os.environ["PRIVATE_KEY"]).read())
signature_object = pkcs1_15.new(private_key)
signature = signature_object.sign(hash)

public_key = RSA.import_key(open(os.environ["PUBLIC_KEY"]).read())

daemon = Pyro5.api.Daemon()
uri = daemon.register(Client)
print("Ready. Client uri =", uri)

server = Pyro5.api.Proxy("PYRO:obj_2831bffb8c7146eba4170354f4dff86c@localhost:32835")
key_base64 = base64.b64encode(public_key.export_key()).decode("utf-8")
server.register(key_base64, uri)


daemon.requestLoop()