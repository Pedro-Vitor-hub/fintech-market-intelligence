import os
import redis
from redis import Redis
from dotenv import load_dotenv

load_dotenv()

# Classe publica para estabelecer a conexão ao Redis
class RedisConnectionHandler:
    def __init__(self) -> None:
        self.__host   = os.getenv("REDIS_HOST")
        self.__port   = int(os.getenv("REDIS_PORT"))
        self.__decode = os.getenv("REDIS_DECODE", "true").lower() == "true"
        self.__db     = int(os.getenv("REDIS_DB"))
        self.__connection = None

    # Metodo que valida e retorna a conexão
    def connection(self) -> Redis | None:
        self.__connection = Redis(
            host=self.__host,
            port=self.__port,
            decode_responses=self.__decode,
            db=self.__db
        )
        try:
            response = self.__connection.ping()
            print(f"✅ Redis conectado: {response}")
        except redis.exceptions.ConnectionError:        # ← corrigido: era Redis.exceptions (crash)
            print("❌ Não foi possível conectar ao Redis")
            return None

        return self.__connection

    def get_connection(self) -> Redis | None:
        return self.__connection