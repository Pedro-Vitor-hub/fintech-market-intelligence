import requests
import redis
import os
import time
from dotenv import load_dotenv
from models.connections.redis_connection import RedisConnectionHandler
from models.connections.mongodb_connection import MongoDBConnectionHandler
from services.cotacaorepository import CotacaoRepository
from services.cassandra_services import conectar_cassandra, setup_cassandra, salvar_no_cassandra
from services.neo4j_services import notificar_investidores

load_dotenv()

# ── URLs das duas moedas
MOEDAS = [
    {
        "url"   : os.getenv("BITCOIN"),   # https://...?symbol=BTCUSDT
        "symbol": "BTCUSDT",
        "moeda" : "BTC",
        "par"   : "BTC/USD",
        "nome"  : "Bitcoin",
    },
    {
        "url"   : os.getenv("ETHEREUM"),  # https://...?symbol=ETHUSDT
        "symbol": "ETHUSDT",
        "moeda" : "ETH",
        "par"   : "ETH/USD",
        "nome"  : "Ethereum",
    },
]

# ── Conexões (estabelecidas uma única vez ao importar o módulo) ───────────────
redis_conn = RedisConnectionHandler().connection()

mongo = MongoDBConnectionHandler()
db    = mongo.valid_connection()['cotacao']
repo  = CotacaoRepository(db, redis_conn)

cassandra_session = conectar_cassandra()
if cassandra_session:
    setup_cassandra(cassandra_session)

# Guarda o último preço de cada moeda para o indicador de volatilidade (bônus)
_ultimos_precos: dict[str, float | None] = {
    "BTCUSDT": None,
    "ETHUSDT": None,
}


def carregar_cotacao(moeda_cfg: dict | None , neo4j_driver) -> dict | None:
    """Executa um ciclo completo de coleta para UMA moeda (BTC ou ETH)."""
    symbol = moeda_cfg["symbol"]
    nome   = moeda_cfg["nome"]

    try:
        print(f"\n🔍 Consultando preço do {nome} ({symbol})...")

        response = requests.get(moeda_cfg["url"], timeout=5)

        if response.status_code != 200:
            print(f"❌ Erro na API: {response.status_code}")
            return None

        dados       = response.json()
        cache_value = redis_conn.get(symbol)

        # ── CACHE HIT 
        if cache_value is not None:
            preco = float(cache_value)
            seta  = _indicador(preco, _ultimos_precos[symbol])
            print(f"⚡ [REDIS] Cache HIT — {symbol}: ${preco:,.2f} {seta}")

        # ── CACHE MISS 
        else:
            preco = float(dados['price'])
            seta  = _indicador(preco, _ultimos_precos[symbol])
            redis_conn.set(symbol, preco, ex=7)
            print(f"🌐 [REDIS] Cache MISS — Fui na API da Binance.")
            print(f"💾 [REDIS] Cache salvo (TTL: 7s) — {symbol}: ${preco:,.2f} {seta}")

        # Atualiza referência de volatilidade para o próximo ciclo
        _ultimos_precos[symbol] = preco

        # ── MONGO 
        repo.salvar_cache_no_mongo(
            symbol=symbol,
            moeda=moeda_cfg["moeda"],
            par=moeda_cfg["par"],
            preco=preco
        )

        # ── CASSANDRA 
        if cassandra_session:
            salvar_no_cassandra(cassandra_session, moeda_cfg["moeda"], symbol, preco)

        # ── NEO4J 
        if neo4j_driver:
            notificar_investidores(neo4j_driver, symbol)

        return {"symbol": symbol, "price": preco}

    except requests.exceptions.ConnectionError:
        print(f"❌ Sem conexão com a internet ({nome})")
    except requests.exceptions.Timeout:
        print(f"❌ API demorou demais para responder ({nome})")
    except redis.exceptions.ConnectionError:
        print("❌ Redis não está rodando — verifique o Docker")

    return None


def carregar_todas_cotacoes(neo4j_driver) -> None:
    """Itera sobre BTC e ETH, processa cada uma e limpa o console ao final."""
    for moeda_cfg in MOEDAS:
        carregar_cotacao(moeda_cfg, neo4j_driver)

    time.sleep(2.3)
    os.system("cls" if os.name == 'nt' else "clear")


def _indicador(preco_novo: float, preco_anterior: float | None) -> str:
    """Retorna o emoji de volatilidade comparando o preço novo com o anterior."""
    if preco_anterior is None:
        return "⚪ (primeira leitura)"
    if preco_novo > preco_anterior:
        return "🟢 (Subiu)"
    if preco_novo < preco_anterior:
        return "🔴 (Caiu)"
    return "🟡 (Estável)"