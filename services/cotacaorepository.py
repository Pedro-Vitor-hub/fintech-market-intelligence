from datetime import datetime


class CotacaoRepository:
    def __init__(self, mongo_db, redis_conn):
        self.__colecao = mongo_db['moedas']
        self.__redis   = redis_conn

    def salvar_cache_no_mongo(self, symbol: str, moeda: str, par: str, preco: float, variacao: float = 0.0) -> dict | None:
        """
        Recebe o preco já resolvido como parâmetro (do Redis ou da API).
        Aceita symbol/moeda/par dinâmicos para suportar BTC e ETH.
        """
        documento = {
            "moeda"      : moeda,
            "par"        : par,
            "symbol"     : symbol,
            "price"      : preco,
            "variacao"   : variacao,
            "data_coleta": datetime.now()
        }

        self.__colecao.insert_one(documento)
        print(f"✅ [MONGO] Payload salvo no Data Lake — {moeda}: ${preco:,.2f}")

        return documento