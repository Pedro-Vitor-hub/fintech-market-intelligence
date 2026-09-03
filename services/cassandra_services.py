from cassandra.cluster import Cluster
from cassandra.policies import RoundRobinPolicy
from datetime import datetime


def conectar_cassandra():
    """Estabelece conexão com o Cassandra e retorna a session."""
    try:
        cluster = Cluster(
            ['127.0.0.1'],
            port=9042,
            load_balancing_policy=RoundRobinPolicy(),
            protocol_version=4
        )
        session = cluster.connect()
        print("✅ Cassandra conectado com sucesso")
        return session
    except Exception as e:
        print(f"❌ Erro ao conectar no Cassandra: {e}")
        return None


def setup_cassandra(session) -> None:
    """
    Cria o keyspace e a tabela caso não existam.

    Modelagem da tabela historico_precos:
        Partition Key  → moeda      agrupa todos os registros do mesmo ativo (BTC, ETH...)
        Clustering Key → data_hora DESC  leituras trazem o mais recente primeiro
    """
    try:
        session.execute("""
            CREATE KEYSPACE IF NOT EXISTS fintech
            WITH replication = {'class': 'SimpleStrategy', 'replication_factor': '1'}
        """)
        session.set_keyspace("fintech")

        session.execute("""
            CREATE TABLE IF NOT EXISTS historico_precos (
                moeda     TEXT,
                data_hora TIMESTAMP,
                symbol    TEXT,
                price     DOUBLE,
                PRIMARY KEY (moeda, data_hora)
            ) WITH CLUSTERING ORDER BY (data_hora DESC)
        """)

        print("✅ [CASSANDRA] Keyspace e tabela prontos")
    except Exception as e:
        print(f"❌ [CASSANDRA] Erro no setup: {e}")


def salvar_no_cassandra(session, moeda: str, symbol: str, price: float) -> None:
    """
    Insere o preço atual na série temporal.
    moeda → ex: 'BTC' ou 'ETH'  (Partition Key — identifica o ativo)
    """
    try:
        session.execute(
            """
            INSERT INTO historico_precos (moeda, data_hora, symbol, price)
            VALUES (%s, %s, %s, %s)
            """,
            (moeda, datetime.now(), symbol, price)
        )
        print(f"📈 [CASSANDRA] Preço de ${price:,.2f} gravado na série temporal ({moeda})")
    except Exception as e:
        print(f"❌ [CASSANDRA] Erro ao salvar: {e}")