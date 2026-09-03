from services.redis_services import carregar_todas_cotacoes
from services.neo4j_services import conectar_neo4j, setup_neo4j

# Cria os nós :Investidor e :Moeda e os relacionamentos [:ACOMPANHA] no grafo.
neo4j_driver = conectar_neo4j()
if neo4j_driver:
    setup_neo4j(neo4j_driver)

## Loop de monitoramento
while True:
    carregar_todas_cotacoes(neo4j_driver=neo4j_driver)