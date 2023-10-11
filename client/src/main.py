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

class Client(object):
    def __init__(self, name: str="", public_key: str="", remote_uri: str=""):
        self.name = name
        self.public_key = public_key
        self.remote_uri = remote_uri

    @Pyro5.api.expose
    def notify_product_emptying(self, product):
        print("Notificação do servidor:")
        print("Produto " + str(product.get("product_name")) + " alcançou o estoque minimo " + str(product.get('quantity_left')))

    @Pyro5.api.expose
    def notify_product_not_being_sold(self, products):
        print("Notificação do servidor:")
        print("Produtos nao sendo vendidos: ",  products)
        
current_user: Client = None

private_key = RSA.import_key(open(os.environ["PRIVATE_KEY"]).read())
public_key = RSA.import_key(open(os.environ["PUBLIC_KEY"]).read())

daemon = Pyro5.api.Daemon()
uri = daemon.register(Client)
import threading
thread = threading.Thread(target=daemon.requestLoop) #test
thread.start()

print("Ready. Client uri =", uri)


server_uri = input("Entre com a URI do servidor: ")
server = Pyro5.api.Proxy(server_uri)
key_base64 = base64.b64encode(public_key.export_key()).decode("utf-8")



def sign_message(message, private_key) -> str:
    message_json = json.dumps(message, sort_keys=True)
    hash = SHA256.new(message_json.encode())
    signature = pkcs1_15.new(private_key).sign(hash)
    message['signature'] = signature.hex()

    return message

def get_current_datetime():
    current_datetime = datetime.datetime.now()
    return current_datetime.strftime("%Y-%m-%d %H:%M:%S")

def read_user_from_input():
    name = input("Entre com seu nome: ")
    public_key = input("Entre com sua chave publica: ")
    remote_uri = input("Entre com o URI remoto: ")

    global current_user
    current_user = Client(name=name, public_key=public_key, remote_uri=remote_uri)

    return {'name': name, 'public_key': public_key, 'remote_uri': remote_uri}

def read_new_user_and_send_to_server():
    user_info = read_user_from_input()
    public_key = user_info['public_key']
    remote_uri = user_info['remote_uri']
    server.register_user(public_key, remote_uri)

def read_product_from_input():
    code = input("Entre com o codigo do produto: ")
    name = input("Entre com o nome do produto: ")
    description = input("Entre com a descrição do produto: ")
    quantity = int(input("Entre com a quantidade de produtos: "))
    unit_price = float(input("Entre com o preço da unidade: "))
    minimum_stock = int(input("Entre com o estoque minimo: "))

    product = {
        'code': code,
        'name': name,
        'description': description,
        'quantity': quantity,
        'unit_price': unit_price,
        'minimum_stock': minimum_stock,
        'date': get_current_datetime()
    }

    return product
    
def read_new_product_and_send_to_server():
    if current_user is None:
        return "Erro: deve existir um usuário previamente registrado para fazer requisições."
    product = read_product_from_input()
    signed_product = sign_message(product, private_key)
    return server.store_new_product(signed_product)

def read_product_to_subtract_from_input():
    code = input("Entre com o codigo do produto a ser subtraido: ")
    quantity_to_subtract = int(input("Entre com a quantidade a ser subtraida: "))

    subtract_request = {
        'code': code,
        'quantity': quantity_to_subtract,
        'date': get_current_datetime()
    }
    return subtract_request

def read_product_to_subtract_and_send_to_server():
    if current_user is None:
        return "Erro: deve existir um usuário previamente registrado para fazer requisições."
    subtract_request = read_product_to_subtract_from_input()
    signed_subtract_request = sign_message(subtract_request, private_key)
    return server.subtract_product(signed_subtract_request)

def check_if_there_is_a_user_registered():
    if current_user == None:
        print("Erro: deve existir um usuário previamente registrado para fazer requisições.")
        return False
    else:
        return True


while True:
    print("\nMenu:")
    print("1. Registrar Usuario")
    print("2. Armazenar Produto")
    print("3. Lançamento de saida de produto")
    print("4. Listar produtos em estoque")
    print("5. Mostrar fluxo do estoque por periodo")
    print("6. Mostrar produtos sem movimentação por periodo")
    print("7. Sair")

    choice = input("Entre com a sua opção: ")

    if choice == '1':
        read_new_user_and_send_to_server()
        response = server.register_user(key_base64, uri)
        print(response)
    elif choice == '2':
        response = read_new_product_and_send_to_server()
        print(response)
    elif choice == '3':
        response = read_product_to_subtract_and_send_to_server()
        print(response)
    elif choice == '4':
        if check_if_there_is_a_user_registered():
            response = server.get_products_in_stock()
            print("Produtos em estoque: ", response)
    elif choice == '5':
        if check_if_there_is_a_user_registered():
            seconds = int(input("Entre com o tempo em segundos: "))
            products = server.get_stock_flow(seconds)
            print(products)
    elif choice == '6':
        if check_if_there_is_a_user_registered():
            seconds = int(input("Entre com o tempo em segundos: "))
            products = server.get_products_without_movimentation_by_period(seconds)
            print(products)
    elif choice == '7':
        thread.stop()
        exit(0)
    else:
        print("Opção Inválida.")