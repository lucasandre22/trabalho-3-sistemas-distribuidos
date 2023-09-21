import Pyro5.api
import base64
import os
from Crypto.PublicKey.RSA import RsaKey, import_key 

os.environ["PYRO_LOGFILE"] = ".pyro.log"
os.environ["PYRO_LOGLEVEL"] = "DEBUG"

Pyro5.api.config.SERIALIZER="marshal"

class Server:
    client_uri: str
    public_key: str

    @Pyro5.api.expose
    def register(self, public_key, uri):
        print("public key from the client: " + str(public_key))
        print("URI from the client: " + str(uri))
        self.client_uri = uri
        self.public_key = self.restore_key(public_key=public_key).export_key()
        print(self.public_key)

    def restore_key(self, public_key):
        return import_key(base64.b64decode(public_key))

    def verifySignature(self):
        print("register")

daemon = Pyro5.api.Daemon()             # make a Pyro daemon
uri = daemon.register(Server)    # register the greeting maker as a Pyro object

print("Ready. Object uri =", uri)       # print the uri so we can use it in the client later
daemon.requestLoop()