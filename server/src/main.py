import Pyro5.api

@Pyro5.api.expose
class Server:

    def register(self, public_key, uri):
        print("public key from the client: " + str(public_key))
        print("URI from the client: " + str(uri))

    def verifySignature(self):
        print("register")

daemon = Pyro5.api.Daemon()             # make a Pyro daemon
uri = daemon.register(Server)    # register the greeting maker as a Pyro object

print("Ready. Object uri =", uri)       # print the uri so we can use it in the client later
daemon.requestLoop()