from neo4j import GraphDatabase
from datetime import datetime


# Investidores fictícios — cada um acompanha AMBAS as moedas
INVESTIDORES = ["Alice", "Bob", "Carlos", "Diana", "Eduardo"]

# Moedas monitoradas
MOEDAS = [
    {"simbolo": "BTCUSDT", "nome": "Bitcoin"},
    {"simbolo": "ETHUSDT", "nome": "Ethereum"},
]


def conectar_neo4j():
    """Estabelece conexão com o Neo4j via Bolt e retorna o driver."""
    try:
        driver = GraphDatabase.driver(
            "bolt://localhost:7687",
            auth=("neo4j", "senha123")
        )
        driver.verify_connectivity()
        print("✅ Neo4j conectado com sucesso")
        return driver
    except Exception as e:
        print(f"❌ Erro ao conectar no Neo4j: {e}")
        return None


def setup_neo4j(driver) -> None:
    """
    Cria os nós :Moeda para BTC e ETH, os nós :Investidor,
    e os relacionamentos [:ACOMPANHA] de cada investidor para CADA moeda.
    Usa MERGE — idempotente, pode rodar múltiplas vezes sem duplicar.
    """
    try:
        with driver.session() as session:
            # Cria os nós das duas moedas
            for moeda in MOEDAS:
                session.run(
                    "MERGE (:Moeda {simbolo: $simbolo, nome: $nome})",
                    simbolo=moeda["simbolo"], nome=moeda["nome"]
                )

            # Para cada investidor, cria o nó e vincula às duas moedas
            for nome in INVESTIDORES:
                for moeda in MOEDAS:
                    session.run(
                        """
                        MERGE (i:Investidor {nome: $nome})
                        WITH i
                        MATCH (m:Moeda {simbolo: $simbolo})
                        MERGE (i)-[:ACOMPANHA]->(m)
                        """,
                        nome=nome, simbolo=moeda["simbolo"]
                    )

        print(f"✅ [NEO4J] Setup concluído — {len(INVESTIDORES)} investidores vinculados a BTC e ETH")
    except Exception as e:
        print(f"❌ [NEO4J] Erro no setup: {e}")


def notificar_investidores(driver, symbol: str) -> None:
    """
    Consulta quais investidores acompanham a moeda passada (BTC ou ETH)
    e grava ultima_notificacao no relacionamento [:ACOMPANHA] (bônus).
    """
    try:
        agora = datetime.now().isoformat()
        with driver.session() as session:
            resultado = session.run(
                """
                MATCH (i:Investidor)-[r:ACOMPANHA]->(m:Moeda {simbolo: $simbolo})
                SET r.ultima_notificacao = $agora
                RETURN i.nome AS nome
                """,
                simbolo=symbol, agora=agora
            )
            nomes = [reg["nome"] for reg in resultado]

        if nomes:
            lista = ", ".join(nomes)
            print(f"🔔 [NEO4J] Notificando investidores de {symbol}: {lista}")
        else:
            print(f"⚠️  [NEO4J] Nenhum investidor encontrado para {symbol}")

    except Exception as e:
        print(f"❌ [NEO4J] Erro ao notificar: {e}")