# Pyro: talk to objets over the network with minimal effor

Pyro utiliza URI para identificar objetos (criada automaticamente quando registra o objeto)   
Para acessar um objeto Pyro, precisa do proxy (transfere a chamda para o computador que contém o objeto real)    

#### Pyro Daemon (precisa no servidor e no client)
- listener a espera das invocações remotas
- objetos precisam ser registrados no daemon, o registro retorna a URI (chave para acessar o objeto)

#### Serviço de nomes é opcional, mapeia nome do app para a URI

uri_pyro = daemon.register()
servio_nomes = ns_lookup()
servico_nomes.register("nome_objeto", uri_pyro)

#### URI o objeto pode retonar, ou o serviço de nomes

Com a URI do objeto, tem o proxy.

##### Client

nome_objeto - Pyro5.api.Proxy(uri_pyro)
nome_objeto.method()

#### Para expor uma classe ou método, anotar com @expose


#### Métodos das notificações no cliente podem ser marcados com @callback (método reverso para notificações)

#### What to do
#1. First, client register itself and get URI;
#2. Pass URI and public key to server
#3. Server gets client, stores the public key
#4. Client needs to get the server URI (can use the name service) (the two sides has request loops)

#5. User needs to interact with application

Pyro5.api,config.SERIALIZER="marshal"

Pyro5.server.behavior(instance_mode="single")