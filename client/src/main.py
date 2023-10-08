import Pyro5.api
import os
import base64
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from dotenv import load_dotenv
import datetime
import json

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

def read_subtract_input():
    code = input("Enter the product code to subtract: ")
    quantity_to_subtract = int(input("Enter the quantity to subtract: "))
    current_datetime = datetime.datetime.now()
    formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M:%S")

    subtract_request = {
        'code': code,
        'quantity': quantity_to_subtract,
        'date': formatted_datetime
    }

    return subtract_request

def subtract_product():
    subtract_request = read_subtract_input()
    signed_subtract_request = sign_product(subtract_request, private_key)
    response = server.subtract_product(signed_subtract_request)
    print(response)


def sign_product(product, private_key):
    product_json = json.dumps(product, sort_keys=True)
    hash = SHA256.new(product_json.encode())
    signature = pkcs1_15.new(private_key).sign(hash)
    product['signature'] = signature.hex()

    return product

def send_signed_product(server, signed_product):
    response = server.store_new_product(signed_product)
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

server = Pyro5.api.Proxy("PYRO:obj_07444d9733eb49eb9b8976ded660baf1@localhost:61765")
key_base64 = base64.b64encode(public_key.export_key()).decode("utf-8")

products = []
#add product
# product = read_product_from_input()
# signed_product = sign_product(product, private_key)
# response = send_signed_product(server, signed_product)
# print(response)

while True:
    print("\nMenu:")
    print("1. Registrar Usuario")
    #necessario ter um usuario antes de por produto
    print("2. Lançamento de entrada de produto")
    print("3. Lançamento de saida de produto")
    print("4. Periodo de tempo")
    print("5. Quit")

    choice = input("Enter your choice: ")

    if choice == '1':
        #user_info = read_user_from_input()
        #public_key = user_info['public_key']
        #remote_uri = user_info['remote_uri']
        #server.register(public_key, remote_uri)
        server.register(key_base64, uri)  
    elif choice == '2':
        product = read_product_from_input()
        signed_product = sign_product(product, private_key)
        response = send_signed_product(server, signed_product)
        print(response)  
    elif choice == '3':
        subtract_product()
    elif choice == '4':
        seconds_to_subtract = int(input("Enter the number of seconds to subtract: "))
        products = server.get_products_after_seconds(seconds_to_subtract)
        print(products)
    elif choice == '5':
        print("Sair")
        break
    else:
        print("Invalid choice. Please try again.")


daemon.requestLoop()