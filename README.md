# 🔥 GásRio — Guia de Instalação e Uso

## Pré-requisitos
- Python 3.8+
- PostgreSQL instalado e rodando
- pip

---

## 1. Instalar dependências Python

```bash
pip install psycopg2-binary faker
```

---

## 2. Criar o banco de dados no PostgreSQL

Abra o **pgAdmin** ou o **psql** e execute:

```sql
CREATE DATABASE distribuidora_gas;
```

---

## 3. Criar as tabelas (Schema)

No pgAdmin, conecte ao banco `distribuidora_gas` e execute o arquivo:

```
01_schema.sql
```

Ou via terminal:
```bash
psql -U postgres -d distribuidora_gas -f 01_schema.sql
```

---

## 4. Popular os dados (15.000+ registros)

Abra o arquivo `02_popular_dados.py` e ajuste a senha se necessário:

```python
DB_CONFIG = {
    "host":     "localhost",
    "port":     5432,
    "dbname":   "distribuidora_gas",
    "user":     "postgres",
    "password": "postgres"  # <-- ajuste aqui
}
```

Execute:
```bash
python 02_popular_dados.py
```

⏱️ Tempo estimado: 2–5 minutos

---

## 5. Executar as análises de gargalo

No pgAdmin ou psql:
```
03_analises.sql
```

Ou via terminal:
```bash
psql -U postgres -d distribuidora_gas -f 03_analises.sql
```

---

## 6. Visualizar o Dashboard

Abra o arquivo no navegador:
```
[🔗 Clique Aqui para ver o Dashboard](https://jottamarcos.github.io/gasrio-analytics/)
```

---

## Estrutura do Projeto

```
distribuidora_gas/
├── 01_schema.sql          → 17 tabelas + índices
├── 02_popular_dados.py    → 15.000+ registros realistas
├── 03_analises.sql        → 13 queries analíticas
├── 04_dashboard.html      → Dashboard interativo
└── LEIAME.md              → Este arquivo
```

## Tabelas criadas (17)

| Tabela                    | Registros |
|---------------------------|-----------|
| filiais                   | 6         |
| funcionarios              | ~180      |
| veiculos                  | ~37       |
| manutencoes_veiculos      | ~400      |
| fornecedores              | 6         |
| produtos                  | 8         |
| estoque                   | 48        |
| movimentacoes_estoque     | 5.000     |
| clientes                  | 3.000     |
| pedidos                   | 10.000    |
| itens_pedido              | ~12.000   |
| compras                   | 200       |
| itens_compra              | ~400      |
| contas_receber            | ~1.500    |
| ocorrencias               | 800       |
| botijoes_clientes         | 2.000     |
| historico_precos          | ~70       |
| multas                    | 150       |
| avaliacoes                | 3.000     |
| **TOTAL**                 | **~39.000** |

---

## Gargalos identificados nas análises

1. 🔴 Bangu e Madureira com taxa de entrega crítica (66–69%)
2. 🔴 Inadimplência acima de 25% em Zona Norte/Oeste
3. 🟡 11 combinações filial/produto abaixo do estoque mínimo
4. 🟡 700 botijões não devolvidos (~R$ 73.500 imobilizado)
5. 🟡 12,5% de cancelamentos (meta: <8%)
6. 🔴 2 veículos com custo >R$ 120/pedido (média: R$ 45)
