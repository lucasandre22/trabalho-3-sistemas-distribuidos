# saved as greeting-client.py
import Pyro5.api

@Pyro5.api.expose
class Client(object):

    def notifyProductEmptying(self):
        print("")

    def notifyProductNotDelivery(self):
        print("")

daemon = Pyro5.api.Daemon() 
uri = daemon.register(Client)
print("Ready. Object uri =", uri)

server = Pyro5.api.Proxy("PYRO:obj_35993f821b7f473799c5468117513582@localhost:35963")     # get a Pyro proxy to the server
print(server.register(uri))   # call method normally

daemon.requestLoop()