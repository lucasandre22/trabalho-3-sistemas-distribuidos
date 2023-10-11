import Pyro5.api
import base64
import os
import json
import threading
from Crypto.PublicKey.RSA import RsaKey, import_key 
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from datetime import datetime, timedelta

os.environ["PYRO_LOGFILE"] = ".pyro.log"
os.environ["PYRO_LOGLEVEL"] = "DEBUG"

Pyro5.api.config.SERIALIZER="marshal"

PERIOD_IN_SECONDS_TO_NOTIFY_CLIENT_PRODUCT_NOT_BEING_SOLD: int = 120
current_user: str = None

class ServerClient(object):
    def __init__(self, public_key, uri):
        self.public_key = public_key
        self.uri = uri

    def get_uri(self) -> str:
        return self.uri
    
    def get_public_key(self) -> str:
        return self.public_key

class Server:
    client_uri: str
    public_key: str
    products = []
    users = {}
    stock_flow = []
    
    def __init__(self):
        #thread to monitor products
        thread = threading.Thread(target=self.start_monitoring_products_not_being_sold) 
        thread.start()

    @Pyro5.api.expose
    def register_user(self, public_key, uri):
        try:
            if public_key in self.users:
                raise Exception("Usuario já registrado.")
            self.users[public_key]: dict[str, ServerClient] = ServerClient(public_key, uri)
            global current_user
            current_user = public_key
            return {"status": "success", "message": "Success: User registered"}
        except Exception as e:
            return {"status": "error", "message" : str(e)}

    def restore_key(self, public_key):
        return import_key(base64.b64decode(public_key))

    def verify_signature(self, json_product):
        try:
            client_public_key = RSA.import_key(self.restore_key(public_key=self.users.get(current_user).get_public_key()).export_key())

            signature_hex = json_product.get('signature', '')
            signature = bytes.fromhex(signature_hex)

            product_json = json_product.copy()
            product_json.pop('signature', None) 
            product_json_str = json.dumps(product_json, sort_keys=True)
            hash = SHA256.new(product_json_str.encode())

            pkcs1_15.new(client_public_key).verify(hash, signature)
            return True
        except Exception as e:
            print(f"Erro verificando assinatura: {str(e)}")
            return False

    def notify_client_product_minimum_stock(self, product):
        print("Produto atingiu estoque mínimo! Notificar cliente.")
        client_remote_uri = self.users.get(current_user).get_uri()
        client = Pyro5.api.Proxy(client_remote_uri)
        client.notify_product_emptying({ "product_name": product["name"], "quantity_left": product['quantity'] })

    def notify_client_product_not_being_sold(self, products):
        print("Há produtos não sendo vendidos! Notificar cliente.")
        client_remote_uri = self.users.get(current_user).get_uri()
        client = Pyro5.api.Proxy(client_remote_uri)
        client.notify_product_not_being_sold(products)

    def start_monitoring_products_not_being_sold(self) -> [str]:
        import time
        print("Começando a monitorar produtos...")
        while True:
            time.sleep(PERIOD_IN_SECONDS_TO_NOTIFY_CLIENT_PRODUCT_NOT_BEING_SOLD)
            products_not_being_sold = self.get_products_without_movimentation_by_period(PERIOD_IN_SECONDS_TO_NOTIFY_CLIENT_PRODUCT_NOT_BEING_SOLD)

            if products_not_being_sold:
                self.notify_client_product_not_being_sold(products_not_being_sold)

    @Pyro5.api.expose
    def get_products_without_movimentation_by_period(self, period_in_seconds: int):
        products_with_no_movimentation = []
        current_datetime = datetime.now()
        for product in self.products:
            if product.get('last_time_sold') is not None:
                last_time_sold = product.get('last_time_sold')
                time_period = timedelta(seconds=period_in_seconds)
                result_datetime = current_datetime - time_period

                if last_time_sold <= result_datetime:
                    products_with_no_movimentation.append({ "product_name": product["name"],
                                                        "code": product["code"],
                                                        "last_movimentation": str(product["last_time_sold"]) })
        return products_with_no_movimentation

    @Pyro5.api.expose
    def get_stock_flow(self, period_in_seconds: int):
        stock_flow_within_period = []
        current_datetime = datetime.now()
        
        # Reversed because the last updated events goes at the end
        for stock_event in reversed(self.stock_flow):
            event_time = stock_event.get('time')
            time_period = timedelta(seconds=period_in_seconds)
            result_datetime = current_datetime - time_period

            if event_time >= result_datetime:
                stock_flow_within_period.append({"operation": stock_event["operation"], "quantity": stock_event["quantity"] })
            else:
                break
        return stock_flow_within_period

    @Pyro5.api.expose
    def store_new_product(self, json_product):
        if self.verify_signature(json_product):
            product_code = json_product.get('code')
            quantity_to_store = json_product.get('quantity')
            for product in self.products:
                if product['code'] == product_code:
                    product['quantity'] += quantity_to_store
                    json_product['quantity'] = product['quantity']
                    print(f"Adicionado {quantity_to_store} unidades para o produto com codigo: {product_code}.")
                    print(self.products)
                    break
            else:
                #insere novo campo para indicar quando um produto foi vendido
                json_product["last_time_sold"] = datetime.now()
                self.products.append(json_product)
                print(f"Added a new product with code {product_code}.")

            self.stock_flow.append({"operation": "product stored", "quantity": quantity_to_store, "time": datetime.now()})
            return 'Sucesso: produto armazenado.'
        else:
            return 'Erro: assinatura invalida'

    @Pyro5.api.expose
    def subtract_product(self, json_product):

        if self.verify_signature(json_product):

            product_code = json_product.get('code')
            quantity_to_subtract = json_product.get('quantity')
            
            print("Codigo dos produtos:")
            for product in self.products:
                print(product['code'])
                if product['code'] == product_code:
                    current_quantity = product.get('quantity')
                    if current_quantity >= quantity_to_subtract:
                        product['quantity'] -= quantity_to_subtract
                        self.stock_flow.append({"operation": "product subtracted", "quantity": quantity_to_subtract, "time": datetime.now()})
                        print(f"Subtracted {quantity_to_subtract} units from product with code {product_code}.")

                        product["last_time_sold"] = datetime.now()

                        if product['quantity'] <= product['minimum_stock']:
                            self.notify_client_product_minimum_stock(product)

                        print(self.products)
                        return 'Sucesso: Produto subtraido.'
                    else:
                        return 'Erro: Não há produtos suficientes para subtrair.'
            return 'Erro: Produto não encontrado.'

        else:
            return 'Erro: Assinatura invalida'
    
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