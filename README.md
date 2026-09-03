# 📊 fintech-market-intelligence

O sistema monitora cotações de **Bitcoin e Ethereum** em tempo real e as distribui para quatro bancos de dados NoSQL simultaneamente, cada um com um propósito específico — conceito de **Persistência Poliglota**.

---

## 🏗️ Arquitetura

```
Binance API (BTC + ETH)
         │
         ▼
    [ Redis ] ◄──── Cache Hit? ──── Sim ───► retorna preço em cache
         │
      Cache Miss
         │
         ├──► [ MongoDB ]   → Data Lake (log bruto com timestamp)
         ├──► [ Cassandra ] → Série temporal (histórico de preços)
         └──► [ Neo4j ]     → Grafo de investidores (sistema de alertas)
```

| Banco | Função |
|---|---|
| **Redis** | Cache de cotação com TTL — baixíssima latência |
| **MongoDB** | Data Lake — log bruto de cada cotação coletada |
| **Cassandra** | Série temporal — histórico otimizado para gráficos |
| **Neo4j** | Grafo de investidores — quem acompanha qual moeda |

---

## 🗂️ Estrutura do Projeto

```
fintech-market-intelligence/
│
├── models/
│   └── connections/
│       ├── redis_connection.py       # Conexão com o Redis
│       └── mongodb_connection.py     # Conexão com o MongoDB
│
├── services/
│   ├── redis_services.py             # Lógica principal do loop (Cache + fluxo)
│   ├── cotacaorepository.py          # Repositório de cotações (MongoDB)
│   ├── cassandra_services.py         # Conexão, setup e insert no Cassandra
│   └── neo4j_services.py             # Conexão, setup e queries no Neo4j
│
├── run.py                            # Ponto de entrada da aplicação
├── docker-compose.yaml               # Sobe os 4 bancos de dados
├── requirements.txt                  # Dependências Python
├── .env.example                      # Modelo das variáveis de ambiente
└── README.md
```

---

## ⚙️ Pré-requisitos

- [Docker](https://www.docker.com/) e Docker Compose instalados
- Python 3.11+

---

## 🚀 Como rodar

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/fintech-market-intelligence.git
cd fintech-market-intelligence
```

### 2. Configure as variáveis de ambiente

Copie o arquivo de exemplo e preencha com seus valores:

Conteúdo do `.env`:

```env
# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_DECODE=true

# MongoDB
MONGO_USERNAME=admin
MONGO_PASSWORD=senha123

# Binance API
BITCOIN=https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT
ETHEREUM=https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT
```

### 3. Suba os containers Docker

```bash
docker-compose up -d
```

> ⚠️ O Cassandra leva cerca de 30–60 segundos para estar pronto após subir. Aguarde antes de rodar o script.

### 4. Instale as dependências Python

```bash
pip install -r requirements.txt
```

### 5. Execute o monitor

```bash
python run.py
```

---

## 🖥️ Exemplo de saída no terminal

```
✅ Redis conectado: True
✅ MongoDB conectado com sucesso
✅ Cassandra conectado com sucesso
✅ [CASSANDRA] Keyspace e tabela prontos
✅ Neo4j conectado com sucesso
✅ [NEO4J] Setup concluído — 5 investidores vinculados a BTC e ETH

🔍 Consultando preço do Bitcoin (BTCUSDT)...
🌐 [REDIS] Cache MISS — Fui na API da Binance.
💾 [REDIS] Cache salvo (TTL: 7s) — BTCUSDT: $98,432.00 🟢 (Subiu)
✅ [MONGO] Payload salvo no Data Lake — BTC: $98,432.00
📈 [CASSANDRA] Preço de $98,432.00 gravado na série temporal (BTC)
🔔 [NEO4J] Notificando investidores de BTCUSDT: Alice, Bob, Carlos, Diana, Eduardo

🔍 Consultando preço do Ethereum (ETHUSDT)...
⚡ [REDIS] Cache HIT — ETHUSDT: $3,210.00 🔴 (Caiu)
✅ [MONGO] Payload salvo no Data Lake — ETH: $3,210.00
📈 [CASSANDRA] Preço de $3,210.00 gravado na série temporal (ETH)
🔔 [NEO4J] Notificando investidores de ETHUSDT: Alice, Bob, Carlos, Diana, Eduardo
```

---

## 🗄️ Modelagem dos Bancos

### Redis
- **Chaves:** `BTCUSDT` e `ETHUSDT`
- **Valor:** preço atual como string
- **TTL:** 7 segundos

### MongoDB — coleção `moedas`
```json
{
  "moeda": "BTC",
  "par": "BTC/USD",
  "symbol": "BTCUSDT",
  "price": 98432.00,
  "variacao": 0.0,
  "data_coleta": "2025-03-04T14:22:00.000Z"
}
```

### Cassandra — tabela `historico_precos`
```sql
PRIMARY KEY (moeda, data_hora)
-- Partition Key  → moeda          (separa registros de BTC e ETH)
-- Clustering Key → data_hora DESC (mais recente primeiro)
```

### Neo4j — Grafo
```
(:Investidor {nome: "Alice"}) -[:ACOMPANHA {ultima_notificacao: "..."}]-> (:Moeda {simbolo: "BTCUSDT"})
(:Investidor {nome: "Alice"}) -[:ACOMPANHA {ultima_notificacao: "..."}]-> (:Moeda {simbolo: "ETHUSDT"})
```

Cada investidor acompanha **ambas** as moedas. A propriedade `ultima_notificacao` é atualizada a cada ciclo do loop.

---

## 📦 Dependências

| Biblioteca | Uso |
|---|---|
| `requests` | Requisições à API da Binance |
| `python-dotenv` | Leitura do arquivo `.env` |
| `redis` | Conexão e operações no Redis |
| `pymongo` | Conexão e operações no MongoDB |
| `cassandra-driver` | Conexão e operações no Cassandra |
| `neo4j` | Conexão e queries Cypher no Neo4j |

---

## 📚 Tecnologias

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![Redis](https://img.shields.io/badge/Redis-7-red?logo=redis)
![MongoDB](https://img.shields.io/badge/MongoDB-7-green?logo=mongodb)
![Cassandra](https://img.shields.io/badge/Cassandra-4.1-blue?logo=apachecassandra)
![Neo4j](https://img.shields.io/badge/Neo4j-5-008CC1?logo=neo4j)
![Docker](https://img.shields.io/badge/Docker-Compose-blue?logo=docker)
