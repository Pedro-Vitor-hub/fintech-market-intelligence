import os
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

load_dotenv()

# Classe publica que valida e conecta no MongoDB
class MongoDBConnectionHandler:
    def __init__(self) -> None:
        self.__connection = MongoClient(
            "mongodb://{}:{}@localhost:27017/".format(
                os.getenv("MONGO_USERNAME"),
                os.getenv("MONGO_PASSWORD")
            ),
            serverSelectionTimeoutMS=3000  # Esperar 3s antes de dar erro
        )

    def valid_connection(self) -> MongoClient | None:
        """Testa a conexão e retorna o MongoClient se estiver ok, ou None."""
        try:
            self.__connection.server_info()
            print("✅ MongoDB conectado com sucesso")
            return self.__connection
        except ServerSelectionTimeoutError:
            print("❌ Timeout — MongoDB não encontrado ou fora do ar")
        except ConnectionFailure:
            print("❌ Falha na conexão com o MongoDB")
        except Exception as e:
            print(f"❌ Erro inesperado: {e}")

        return None