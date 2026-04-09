"""
============================================================
DISTRIBUIDORA DE GÁS RJ — POPULADOR DE DADOS
============================================================
Requisitos: pip install psycopg2-binary faker
Uso: python 02_popular_dados.py
============================================================
"""

import psycopg2
import random
import string
from datetime import date, datetime, timedelta
from decimal import Decimal
from faker import Faker

fake = Faker('pt_BR')
random.seed(42)

# ============================================================
# CONFIGURAÇÃO DE CONEXÃO
# ============================================================
DB_CONFIG = {
    "host":     "localhost",
    "port":     5432,
    "dbname":   "distribuidora_gas",
    "user":     "postgres",
    "password": "SUA SENHA" 
}

def conectar():
    return psycopg2.connect(**DB_CONFIG)

def rand_date(start: date, end: date) -> date:
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))

def rand_datetime(start: date, end: date) -> datetime:
    d = rand_date(start, end)
    h = random.randint(7, 19)
    m = random.choice([0, 15, 30, 45])
    return datetime(d.year, d.month, d.day, h, m)

def gerar_cpf():
    nums = [random.randint(0, 9) for _ in range(9)]
    d1 = 11 - (sum((10 - i) * nums[i] for i in range(9)) % 11)
    d1 = 0 if d1 >= 10 else d1
    nums.append(d1)
    d2 = 11 - (sum((11 - i) * nums[i] for i in range(10)) % 11)
    d2 = 0 if d2 >= 10 else d2
    nums.append(d2)
    n = ''.join(map(str, nums))
    return f"{n[:3]}.{n[3:6]}.{n[6:9]}-{n[9:]}"

def gerar_cnpj():
    n = [random.randint(0, 9) for _ in range(12)]
    pesos1 = [5,4,3,2,9,8,7,6,5,4,3,2]
    d1 = 11 - (sum(n[i]*pesos1[i] for i in range(12)) % 11)
    d1 = 0 if d1 >= 10 else d1
    n.append(d1)
    pesos2 = [6,5,4,3,2,9,8,7,6,5,4,3,2]
    d2 = 11 - (sum(n[i]*pesos2[i] for i in range(13)) % 11)
    d2 = 0 if d2 >= 10 else d2
    n.append(d2)
    s = ''.join(map(str, n))
    return f"{s[:2]}.{s[2:5]}.{s[5:8]}/{s[8:12]}-{s[12:]}"

print("=" * 60)
print("  DISTRIBUIDORA DE GÁS RJ — CARGA DE DADOS")
print("=" * 60)

conn = conectar()
cur  = conn.cursor()

# ============================================================
# 1. FILIAIS (6 fixas)
# ============================================================
print("\n[1/17] Inserindo filiais...")

filiais_data = [
    ("Filial Centro",        "Centro",           "Zona Central",  "Rua Primeiro de Março, 120",       "20010-000", "(21) 3200-1001", gerar_cnpj(), "Roberto Mendes",     800, date(2010, 3, 15)),
    ("Filial Barra",         "Barra da Tijuca",  "Zona Oeste",    "Av. das Américas, 4666",           "22640-102", "(21) 3200-1002", gerar_cnpj(), "Carla Souza",        1200, date(2013, 6, 1)),
    ("Filial Madureira",     "Madureira",        "Zona Norte",    "Rua Carolina Machado, 850",        "21310-000", "(21) 3200-1003", gerar_cnpj(), "Jorge Lima",         900, date(2011, 9, 20)),
    ("Filial Campo Grande",  "Campo Grande",     "Zona Oeste",    "Estrada do Mendanha, 2300",        "23080-000", "(21) 3200-1004", gerar_cnpj(), "Patricia Vieira",    1000, date(2014, 2, 10)),
    ("Filial Niterói",       "Icaraí",           "Niterói",       "Rua Gavião Peixoto, 74",           "24230-100", "(21) 3200-1005", gerar_cnpj(), "Marcos Ferreira",    750, date(2015, 7, 5)),
    ("Filial Bangu",         "Bangu",            "Zona Oeste",    "Rua Fonseca, 310",                 "21810-000", "(21) 3200-1006", gerar_cnpj(), "Aline Costa",        850, date(2016, 11, 30)),
]

for f in filiais_data:
    cur.execute("""
        INSERT INTO filiais (nome, bairro, zona, endereco, cep, telefone, cnpj, gerente, capacidade_max, data_abertura)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (cnpj) DO NOTHING
    """, f)
conn.commit()
cur.execute("SELECT id_filial FROM filiais ORDER BY id_filial")
ids_filiais = [r[0] for r in cur.fetchall()]
print(f"   ✓ {len(ids_filiais)} filiais inseridas")

# ============================================================
# 2. FUNCIONÁRIOS (~180)
# ============================================================
print("[2/17] Inserindo funcionários...")

cargos = [
    ("entregador",  2100, 3.5),
    ("entregador",  2100, 3.5),
    ("entregador",  2100, 3.5),
    ("atendente",   1800, 1.0),
    ("atendente",   1800, 1.0),
    ("supervisor",  3500, 0.5),
    ("tecnico",     2800, 0.0),
    ("gerente",     5500, 0.0),
]

cpfs_usados = set()
ids_funcionarios = []
ids_entregadores = []

for id_f in ids_filiais:
    for cargo, salario_base, comissao in cargos:
        nome = fake.name()
        cpf = gerar_cpf()
        while cpf in cpfs_usados:
            cpf = gerar_cpf()
        cpfs_usados.add(cpf)
        admissao = rand_date(date(2010, 1, 1), date(2023, 12, 31))
        ativo = random.random() > 0.08
        demissao = None if ativo else rand_date(admissao + timedelta(days=90), date(2024, 6, 1))
        salario = round(salario_base * random.uniform(0.95, 1.25), 2)
        cnh = ''.join(random.choices(string.digits, k=11)) if cargo in ('entregador', 'supervisor', 'gerente') else None
        cur.execute("""
            INSERT INTO funcionarios (id_filial, nome, cpf, cargo, salario, comissao_pct,
                                      data_admissao, data_demissao, ativo, cnh, telefone)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id_funcionario, cargo
        """, (id_f, nome, cpf, cargo, salario, comissao, admissao, demissao, ativo, cnh, fake.phone_number()))
        row = cur.fetchone()
        ids_funcionarios.append((row[0], id_f, row[1]))
        if cargo == 'entregador' and ativo:
            ids_entregadores.append((row[0], id_f))

conn.commit()
print(f"   ✓ {len(ids_funcionarios)} funcionários inseridos")

# ============================================================
# 3. VEÍCULOS (~36)
# ============================================================
print("[3/17] Inserindo veículos...")

modelos_veiculos = [
    ("VW Delivery", "Volkswagen", 60),
    ("Ford Cargo",  "Ford",       80),
    ("Fiat Ducato", "Fiat",       50),
    ("Mercedes Sprinter", "Mercedes-Benz", 70),
    ("Iveco Daily", "Iveco",      65),
]
placas_usadas = set()
ids_veiculos = []

for id_f in ids_filiais:
    n_veiculos = random.randint(5, 8)
    for _ in range(n_veiculos):
        modelo, marca, cap = random.choice(modelos_veiculos)
        while True:
            placa = ''.join(random.choices(string.ascii_uppercase, k=3)) + \
                    str(random.randint(0,9)) + \
                    random.choice(string.ascii_uppercase) + \
                    ''.join(random.choices(string.digits, k=2))
            if placa not in placas_usadas:
                placas_usadas.add(placa)
                break
        status = random.choices(['disponivel','em_rota','manutencao','inativo'],
                                 weights=[60,20,15,5])[0]
        cur.execute("""
            INSERT INTO veiculos (id_filial, placa, modelo, marca, ano, capacidade_botijoes,
                                  km_atual, status, data_aquisicao)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id_veiculo
        """, (id_f, placa, modelo, marca, random.randint(2010, 2023),
              cap, random.randint(20000, 180000), status,
              rand_date(date(2010,1,1), date(2023,1,1))))
        ids_veiculos.append((cur.fetchone()[0], id_f))

conn.commit()
print(f"   ✓ {len(ids_veiculos)} veículos inseridos")

# ============================================================
# 4. MANUTENÇÕES (~400)
# ============================================================
print("[4/17] Inserindo manutenções de veículos...")

tipos_manut = ['preventiva','corretiva','revisao']
oficinas = ['Auto Center Silva','Mecânica do João','TruckCar RJ','Oficina Boa Vista','MecaTrans']
cnt = 0
for id_v, _ in ids_veiculos:
    for _ in range(random.randint(3, 8)):
        entrada = rand_date(date(2020,1,1), date(2024,12,1))
        saida   = entrada + timedelta(days=random.randint(1,10))
        tipo    = random.choice(tipos_manut)
        custo   = round(random.uniform(300, 4500), 2) if tipo == 'corretiva' else round(random.uniform(150, 900), 2)
        cur.execute("""
            INSERT INTO manutencoes_veiculos (id_veiculo, tipo, descricao, custo,
                km_na_manutencao, data_entrada, data_saida, oficina, status)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'concluida')
        """, (id_v, tipo, f"Manutenção {tipo} - {fake.bs()}", custo,
              random.randint(5000, 170000), entrada, saida, random.choice(oficinas)))
        cnt += 1

conn.commit()
print(f"   ✓ {cnt} manutenções inseridas")

# ============================================================
# 5. FORNECEDORES
# ============================================================
print("[5/17] Inserindo fornecedores...")

fornecedores_data = [
    ("Petrobras Distribuidora S.A.",  gerar_cnpj(), "João Alberto",   2, 4.8),
    ("Liquigás Distribuidora S.A.",   gerar_cnpj(), "Ana Cristina",   3, 4.5),
    ("Ultragaz S.A.",                 gerar_cnpj(), "Pedro Rocha",    3, 4.6),
    ("Supergasbras Energia Ltda.",    gerar_cnpj(), "Mariana Lima",   4, 4.2),
    ("Nacional Gás Butano Ltda.",     gerar_cnpj(), "Carlos Meireles",5, 3.9),
    ("GLP Comércio e Serviços Ltda.", gerar_cnpj(), "Rita Carvalho",  4, 4.0),
]

ids_fornecedores = []
for f in fornecedores_data:
    cur.execute("""
        INSERT INTO fornecedores (razao_social, cnpj, contato, telefone, email,
                                   prazo_entrega_dias, avaliacao, ativo)
        VALUES (%s,%s,%s,%s,%s,%s,%s,TRUE) RETURNING id_fornecedor
    """, (f[0], f[1], f[2], fake.phone_number(), fake.email(), f[3], f[4]))
    ids_fornecedores.append(cur.fetchone()[0])

conn.commit()
print(f"   ✓ {len(ids_fornecedores)} fornecedores inseridos")

# ============================================================
# 6. PRODUTOS
# ============================================================
print("[6/17] Inserindo produtos...")

produtos_data = [
    ("GAS-P13",  "Botijão GLP P13 13kg (Residencial)",      "botijao_p13",  13.0,  52.00, 105.00),
    ("GAS-P20",  "Botijão GLP P20 20kg (Comercial Leve)",   "botijao_p20",  20.0,  80.00, 155.00),
    ("GAS-P45",  "Botijão GLP P45 45kg (Comercial)",        "botijao_p45",  45.0, 175.00, 320.00),
    ("GAS-P190", "Botijão GLP P190 190kg (Industrial)",     "botijao_p190", 190.0, 700.00,1200.00),
    ("GAS-GRN",  "GLP Granel (por kg)",                     "granel",         1.0,   4.20,   7.50),
    ("ACES-REG", "Regulador de Pressão Aliança",            "acessorio",      0.3,   15.00,  35.00),
    ("ACES-MAN", "Mangueira GLP 1,20m c/ abraçadeiras",    "acessorio",      0.2,    8.00,  22.00),
    ("ACES-VAL", "Válvula para Botijão P13",                "acessorio",      0.1,   12.00,  28.00),
]

ids_produtos = []
for p in produtos_data:
    cur.execute("""
        INSERT INTO produtos (codigo, descricao, tipo, peso_kg, preco_custo, preco_venda, ativo)
        VALUES (%s,%s,%s,%s,%s,%s,TRUE) RETURNING id_produto
    """, p)
    ids_produtos.append(cur.fetchone()[0])

conn.commit()
print(f"   ✓ {len(ids_produtos)} produtos inseridos")

# ============================================================
# 7. ESTOQUE POR FILIAL
# ============================================================
print("[7/17] Inserindo estoque por filial...")

for id_f in ids_filiais:
    for id_p in ids_produtos:
        qtd = random.randint(5, 450)
        emin = 20 if id_p in ids_produtos[:4] else 5
        emax = random.randint(300, 600)
        cur.execute("""
            INSERT INTO estoque (id_filial, id_produto, quantidade, estoque_minimo, estoque_maximo)
            VALUES (%s,%s,%s,%s,%s) ON CONFLICT (id_filial, id_produto) DO NOTHING
        """, (id_f, id_p, qtd, emin, emax))

conn.commit()
print(f"   ✓ {len(ids_filiais)*len(ids_produtos)} registros de estoque")

# ============================================================
# 8. CLIENTES (~3000)
# ============================================================
print("[8/17] Inserindo clientes (~3000)...")

bairros_rj = [
    ("Copacabana","Zona Sul"), ("Ipanema","Zona Sul"), ("Leblon","Zona Sul"),
    ("Botafogo","Zona Sul"), ("Flamengo","Zona Sul"), ("Catete","Zona Sul"),
    ("Centro","Zona Central"), ("Lapa","Zona Central"), ("Gamboa","Zona Central"),
    ("Tijuca","Zona Norte"), ("Madureira","Zona Norte"), ("Méier","Zona Norte"),
    ("Engenho Novo","Zona Norte"), ("Jacarepaguá","Zona Oeste"),
    ("Barra da Tijuca","Zona Oeste"), ("Campo Grande","Zona Oeste"),
    ("Bangu","Zona Oeste"), ("Santa Cruz","Zona Oeste"),
    ("Icaraí","Niterói"), ("São Francisco","Niterói"), ("Fonseca","Niterói"),
]
canais = ['telefone','telefone','telefone','whatsapp','whatsapp','app','balcao']
docs_usados = set()
ids_clientes = []
ids_clientes_pj = []

for _ in range(3000):
    tipo = random.choices(['PF','PJ'], weights=[75,25])[0]
    bairro, zona = random.choice(bairros_rj)
    id_filial = random.choice(ids_filiais)
    permite_fiado = random.random() < 0.3
    limite_fiado  = round(random.uniform(100, 800), 2) if permite_fiado else 0

    if tipo == 'PF':
        nome = fake.name()
        doc  = gerar_cpf()
    else:
        nome = fake.company() + " " + random.choice(["Ltda.","S.A.","ME","EIRELI"])
        doc  = gerar_cnpj()

    while doc in docs_usados:
        doc = gerar_cpf() if tipo == 'PF' else gerar_cnpj()
    docs_usados.add(doc)

    cadastro = rand_date(date(2018,1,1), date(2024,12,31))
    ativo    = random.random() > 0.10

    cur.execute("""
        INSERT INTO clientes (tipo, nome, cpf_cnpj, telefone, email, endereco, bairro, zona, cep,
                               id_filial_atend, data_cadastro, ativo, permite_fiado, limite_fiado, canal_preferido)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id_cliente
    """, (tipo, nome, doc, fake.phone_number(), fake.email(),
          fake.street_address(), bairro, zona,
          f"{random.randint(20000,23999):05d}-{random.randint(0,999):03d}",
          id_filial, cadastro, ativo, permite_fiado, limite_fiado,
          random.choice(canais)))
    id_c = cur.fetchone()[0]
    ids_clientes.append((id_c, id_filial))
    if tipo == 'PJ':
        ids_clientes_pj.append(id_c)

conn.commit()
print(f"   ✓ {len(ids_clientes)} clientes inseridos")

# ============================================================
# 9. PEDIDOS (~10.000) + ITENS
# ============================================================
print("[9/17] Inserindo pedidos (~10.000)... (pode demorar ~30s)")

status_pesos  = ['entregue','entregue','entregue','entregue',
                  'cancelado','em_rota','pendente','confirmado']
formas_pag    = ['dinheiro','dinheiro','pix','pix','cartao_debito','cartao_credito','fiado']
canais_pedido = ['telefone','telefone','whatsapp','whatsapp','app','balcao']
motivos_canc  = ['cliente_desistiu','produto_indisponivel','endereco_nao_encontrado',
                  'pagamento_recusado','concorrente_preco_menor']

ids_pedidos = []
ids_pedidos_entregues = []

# Mapa filial → funcionários ativos
func_por_filial = {}
entreg_por_filial = {}
veic_por_filial   = {}
for id_fid, id_fi, cargo in ids_funcionarios:
    func_por_filial.setdefault(id_fi, []).append(id_fid)
for id_e, id_fi in ids_entregadores:
    entreg_por_filial.setdefault(id_fi, []).append(id_e)
for id_v, id_fi in ids_veiculos:
    veic_por_filial.setdefault(id_fi, []).append(id_v)

BATCH = 500
pedidos_batch = []
itens_batch   = []

for i in range(10000):
    id_c, id_fi = random.choice(ids_clientes)
    atend_list  = func_por_filial.get(id_fi, [None])
    id_atend    = random.choice(atend_list)
    entreg_list = entreg_por_filial.get(id_fi, [None])
    id_entreg   = random.choice(entreg_list) if entreg_list else None
    veic_list   = veic_por_filial.get(id_fi, [None])
    id_veic     = random.choice(veic_list)

    data_ped    = rand_datetime(date(2021,1,1), date(2024,12,31))
    canal       = random.choice(canais_pedido)
    forma_pag   = random.choice(formas_pag)
    status      = random.choice(status_pesos)

    # Datas de entrega
    prev_h  = random.randint(1, 6)
    data_prev = data_ped + timedelta(hours=prev_h)
    data_real = None
    if status == 'entregue':
        atraso = random.choices([0,0,0,1,2,3], weights=[50,20,10,10,7,3])[0]
        data_real = data_prev + timedelta(hours=atraso * random.randint(1,3))
    elif status == 'em_rota':
        data_real = None

    motivo_canc = random.choice(motivos_canc) if status == 'cancelado' else None

    # Itens do pedido (1-3 produtos)
    n_itens   = random.choices([1,2,3], weights=[70,25,5])[0]
    prods_ped = random.sample(ids_produtos, min(n_itens, len(ids_produtos)))
    valor_tot = 0
    itens_ped = []
    for id_p in prods_ped:
        idx_p  = ids_produtos.index(id_p)
        preco  = float(produtos_data[idx_p][5])
        preco  = round(preco * random.uniform(0.95, 1.05), 2)
        qtd    = random.choices([1,2,3,4], weights=[60,25,10,5])[0]
        valor_tot += preco * qtd
        itens_ped.append((id_p, qtd, preco))

    desconto   = round(valor_tot * random.uniform(0, 0.05), 2) if random.random() < 0.15 else 0
    valor_final = round(valor_tot - desconto, 2)

    cur.execute("""
        INSERT INTO pedidos (id_cliente, id_filial, id_funcionario, data_pedido,
            data_entrega_prevista, data_entrega_real, status, canal, forma_pagamento,
            valor_total, desconto, valor_final, motivo_cancelamento, id_veiculo, id_entregador)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id_pedido
    """, (id_c, id_fi, id_atend, data_ped, data_prev, data_real,
          status, canal, forma_pag, round(valor_tot,2), desconto, valor_final,
          motivo_canc, id_veic, id_entreg))
    id_ped = cur.fetchone()[0]
    ids_pedidos.append((id_ped, id_fi, id_c, status, forma_pag))
    if status == 'entregue':
        ids_pedidos_entregues.append((id_ped, id_c))

    for id_p, qtd, preco in itens_ped:
        cur.execute("""
            INSERT INTO itens_pedido (id_pedido, id_produto, quantidade, preco_unitario)
            VALUES (%s,%s,%s,%s)
        """, (id_ped, id_p, qtd, preco))

    if (i+1) % BATCH == 0:
        conn.commit()
        print(f"   → {i+1}/10000 pedidos...")

conn.commit()
print(f"   ✓ {len(ids_pedidos)} pedidos inseridos")

# ============================================================
# 10. COMPRAS DE FORNECEDOR (~200)
# ============================================================
print("[10/17] Inserindo compras de fornecedor...")

for _ in range(200):
    id_fi   = random.choice(ids_filiais)
    id_forn = random.choice(ids_fornecedores)
    data_ped = rand_date(date(2021,1,1), date(2024,12,1))
    prazo   = random.randint(2,7)
    data_prev = data_ped + timedelta(days=prazo)
    atraso  = random.choices([0,0,0,1,2,3,5], weights=[50,20,10,8,6,4,2])[0]
    data_real = data_prev + timedelta(days=atraso)
    status  = random.choices(['entregue','entregue','atrasado','cancelado','pendente'],
                              weights=[60,15,12,8,5])[0]
    cur.execute("""
        INSERT INTO compras (id_filial, id_fornecedor, data_pedido, data_entrega_prevista,
                              data_entrega_real, status)
        VALUES (%s,%s,%s,%s,%s,%s) RETURNING id_compra
    """, (id_fi, id_forn, data_ped, data_prev, data_real if status!='pendente' else None, status))
    id_comp = cur.fetchone()[0]

    valor_comp = 0
    for id_p in random.sample(ids_produtos[:5], random.randint(1,3)):
        idx_p = ids_produtos.index(id_p)
        preco = float(produtos_data[idx_p][4])
        qtd   = random.randint(50, 300)
        valor_comp += preco * qtd
        cur.execute("""
            INSERT INTO itens_compra (id_compra, id_produto, quantidade, preco_unitario)
            VALUES (%s,%s,%s,%s)
        """, (id_comp, id_p, qtd, preco))

    cur.execute("UPDATE compras SET valor_total=%s WHERE id_compra=%s",
                (round(valor_comp,2), id_comp))

conn.commit()
print(f"   ✓ 200 compras inseridas")

# ============================================================
# 11. CONTAS A RECEBER / FIADO (~1500)
# ============================================================
print("[11/17] Inserindo contas a receber...")

fiado_pedidos = [(id_p, id_c) for id_p, _, id_c, _, fp in ids_pedidos if fp == 'fiado']
random.shuffle(fiado_pedidos)
cnt = 0
for id_ped, id_c in fiado_pedidos[:1500]:
    data_ped_row = rand_date(date(2021,1,1), date(2024,12,31))
    vencimento   = data_ped_row + timedelta(days=random.choice([7,15,30]))
    status_c     = random.choices(['pago','aberto','vencido','renegociado'],
                                   weights=[55,20,18,7])[0]
    data_pag     = None
    if status_c == 'pago':
        data_pag = vencimento + timedelta(days=random.randint(-3, 5))
    juros = round(random.uniform(2,15), 2) if status_c in ('vencido','renegociado') else 0
    cur.execute("""
        INSERT INTO contas_receber (id_pedido, id_cliente, valor, data_vencimento,
                                     data_pagamento, status, juros)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
    """, (id_ped, id_c, round(random.uniform(50,500),2),
          vencimento, data_pag, status_c, juros))
    cnt += 1

conn.commit()
print(f"   ✓ {cnt} contas a receber inseridas")

# ============================================================
# 12. OCORRÊNCIAS (~800)
# ============================================================
print("[12/17] Inserindo ocorrências...")

tipos_ocorr = [
    ('cliente_ausente',     'baixa'),
    ('endereco_errado',     'baixa'),
    ('reclamacao_cliente',  'media'),
    ('avaria_produto',      'media'),
    ('veiculo_quebrado',    'alta'),
    ('vazamento',           'alta'),
    ('acidente',            'critica'),
    ('furto',               'critica'),
    ('atraso_entrega',      'baixa'),
    ('produto_errado',      'media'),
]

cnt = 0
for _ in range(800):
    id_fi    = random.choice(ids_filiais)
    tipo, grav = random.choice(tipos_ocorr)
    id_ped   = random.choice(ids_pedidos)[0] if random.random() > 0.3 else None
    id_c     = random.choice(ids_clientes)[0] if random.random() > 0.4 else None
    id_func  = random.choice(ids_funcionarios)[0]
    data_oc  = rand_datetime(date(2021,1,1), date(2024,12,31))
    status_o = random.choices(['resolvido','resolvido','em_analise','aberto'],
                               weights=[65,10,15,10])[0]
    data_res = None
    if status_o == 'resolvido':
        data_res = data_oc + timedelta(days=random.randint(0,10))
    custo_oc = round(random.uniform(0, 2000), 2) if grav in ('alta','critica') else round(random.uniform(0,300),2)
    notif    = grav == 'critica' and random.random() > 0.3

    cur.execute("""
        INSERT INTO ocorrencias (id_filial, id_pedido, id_cliente, id_funcionario, tipo,
            descricao, gravidade, status, data_ocorrencia, data_resolucao,
            custo_ocorrencia, notificado_orgao)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (id_fi, id_ped, id_c, id_func, tipo,
          f"Ocorrência: {tipo.replace('_',' ')} - {fake.bs()}",
          grav, status_o, data_oc, data_res, custo_oc, notif))
    cnt += 1

conn.commit()
print(f"   ✓ {cnt} ocorrências inseridas")

# ============================================================
# 13. BOTIJÕES COM CLIENTES (~2000)
# ============================================================
print("[13/17] Inserindo controle de botijões...")

cnt = 0
for _ in range(2000):
    id_c, _ = random.choice(ids_clientes)
    id_p    = ids_produtos[0]  # P13 principalmente
    data_emp = rand_date(date(2021,1,1), date(2024,12,31))
    status_b = random.choices(['devolvido','com_cliente','perdido'],
                               weights=[60,35,5])[0]
    data_dev = None
    if status_b == 'devolvido':
        data_dev = data_emp + timedelta(days=random.randint(1,60))
    id_ped_orig = random.choice(ids_pedidos_entregues)[0] if ids_pedidos_entregues else None
    cur.execute("""
        INSERT INTO botijoes_clientes (id_cliente, id_produto, quantidade, data_emprestimo,
                                       data_devolucao, status, id_pedido_origem)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
    """, (id_c, id_p, 1, data_emp, data_dev, status_b, id_ped_orig))
    cnt += 1

conn.commit()
print(f"   ✓ {cnt} registros de botijões inseridos")

# ============================================================
# 14. HISTÓRICO DE PREÇOS (~60)
# ============================================================
print("[14/17] Inserindo histórico de preços...")

motivos_preco = [
    'Reajuste Petrobras', 'Ajuste competitividade', 'Alta do câmbio',
    'Queda do petróleo', 'Reajuste por inflação', 'Promoção sazonal'
]
cnt = 0
for id_p in ids_produtos:
    idx_p = ids_produtos.index(id_p)
    custo_base = float(produtos_data[idx_p][4])
    venda_base = float(produtos_data[idx_p][5])
    for _ in range(random.randint(4, 10)):
        variacao_c = random.uniform(-0.08, 0.15)
        variacao_v = random.uniform(-0.05, 0.18)
        cur.execute("""
            INSERT INTO historico_precos (id_produto, preco_custo_anterior, preco_custo_novo,
                preco_venda_anterior, preco_venda_novo, data_alteracao, motivo)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, (id_p, round(custo_base,2), round(custo_base*(1+variacao_c),2),
              round(venda_base,2), round(venda_base*(1+variacao_v),2),
              rand_date(date(2021,1,1), date(2024,12,31)),
              random.choice(motivos_preco)))
        custo_base = custo_base * (1 + variacao_c)
        venda_base = venda_base * (1 + variacao_v)
        cnt += 1

conn.commit()
print(f"   ✓ {cnt} registros de histórico de preços")

# ============================================================
# 15. MULTAS (~150)
# ============================================================
print("[15/17] Inserindo multas...")

infrações = [
    'Excesso de velocidade', 'Estacionamento irregular', 'Avanço de sinal',
    'Uso de celular', 'Documento irregular', 'Sobrepeso de carga'
]
cnt = 0
for _ in range(150):
    id_v, id_fi = random.choice(ids_veiculos)
    id_func     = random.choice([f for f, fi, c in ids_funcionarios if fi == id_fi] or [ids_funcionarios[0][0]])
    data_inf    = rand_date(date(2021,1,1), date(2024,12,31))
    status_m    = random.choices(['pago','pendente','recorrido'], weights=[55,30,15])[0]
    responsavel = random.choices(['empresa','funcionario'], weights=[70,30])[0]
    cur.execute("""
        INSERT INTO multas (id_veiculo, id_funcionario, data_infracao, tipo_infracao,
                             valor, status, responsavel)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
    """, (id_v, id_func, data_inf, random.choice(infrações),
          round(random.uniform(88, 880), 2), status_m, responsavel))
    cnt += 1

conn.commit()
print(f"   ✓ {cnt} multas inseridas")

# ============================================================
# 16. AVALIAÇÕES (~3000)
# ============================================================
print("[16/17] Inserindo avaliações...")

comentarios_pos = [
    "Entrega rápida, muito satisfeito!",
    "Atendimento excelente, recomendo.",
    "Chegou no horário combinado.",
    "Produto em perfeito estado.",
    "Entregador muito educado.",
]
comentarios_neg = [
    "Atrasou mais de 2 horas.",
    "Entregador foi grosseiro.",
    "Produto veio amassado.",
    "Cobrou diferente do combinado.",
    "Tive que ligar várias vezes.",
]

cnt = 0
pedidos_amostra = random.sample(ids_pedidos_entregues, min(3000, len(ids_pedidos_entregues)))
for id_ped, id_c in pedidos_amostra:
    nota = random.choices(range(1,11), weights=[1,1,2,2,3,5,8,15,20,25])[0]
    coment = random.choice(comentarios_pos) if nota >= 7 else random.choice(comentarios_neg)
    canal_av = random.choice(['app','whatsapp','telefone','site'])
    cur.execute("""
        INSERT INTO avaliacoes (id_pedido, id_cliente, nota, comentario, data_avaliacao, canal_avaliacao)
        VALUES (%s,%s,%s,%s,%s,%s)
    """, (id_ped, id_c, nota, coment,
          rand_datetime(date(2021,1,1), date(2024,12,31)), canal_av))
    cnt += 1

conn.commit()
print(f"   ✓ {cnt} avaliações inseridas")

# ============================================================
# 17. MOVIMENTAÇÕES DE ESTOQUE (~5000)
# ============================================================
print("[17/17] Inserindo movimentações de estoque...")

tipos_mov = ['entrada','saida','ajuste','saida','saida','saida']
motivos_mov = {
    'entrada': ['compra_fornecedor','devolucao_cliente','transferencia_entre_filiais'],
    'saida':   ['venda','perda','transferencia_entre_filiais'],
    'ajuste':  ['inventario','correcao_sistema'],
}
cnt = 0
for _ in range(5000):
    id_fi  = random.choice(ids_filiais)
    id_p   = random.choice(ids_produtos)
    tipo   = random.choice(tipos_mov)
    qtd    = random.randint(1, 50)
    motivo = random.choice(motivos_mov.get(tipo, ['geral']))
    id_func = random.choice([f for f, fi, c in ids_funcionarios if fi == id_fi] or [ids_funcionarios[0][0]])
    cur.execute("""
        INSERT INTO movimentacoes_estoque (id_filial, id_produto, tipo, quantidade,
                                           motivo, data_movimentacao, id_funcionario)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
    """, (id_fi, id_p, tipo, qtd, motivo,
          rand_datetime(date(2021,1,1), date(2024,12,31)), id_func))
    cnt += 1

conn.commit()
print(f"   ✓ {cnt} movimentações inseridas")

# ============================================================
# RESUMO FINAL
# ============================================================
cur.close()
conn.close()

print("\n" + "=" * 60)
print("  CARGA CONCLUÍDA COM SUCESSO!")
print("=" * 60)

tabelas = [
    ("filiais",                  len(ids_filiais)),
    ("funcionarios",             len(ids_funcionarios)),
    ("veiculos",                 len(ids_veiculos)),
    ("manutencoes_veiculos",     "~400"),
    ("fornecedores",             len(ids_fornecedores)),
    ("produtos",                 len(ids_produtos)),
    ("estoque",                  len(ids_filiais)*len(ids_produtos)),
    ("clientes",                 len(ids_clientes)),
    ("pedidos",                  len(ids_pedidos)),
    ("itens_pedido",             "~12.000"),
    ("compras",                  200),
    ("itens_compra",             "~400"),
    ("contas_receber",           1500),
    ("ocorrencias",              800),
    ("botijoes_clientes",        2000),
    ("historico_precos",         "~70"),
    ("multas",                   150),
    ("avaliacoes",               3000),
    ("movimentacoes_estoque",    5000),
]

total = 0
for tabela, qtd in tabelas:
    try:
        total += int(qtd)
    except:
        pass
    print(f"  {tabela:<30} {str(qtd):>8} registros")

print(f"\n  TOTAL ESTIMADO: 15.000+ registros em 17 tabelas")
print("=" * 60)
print("\nPróximo passo: execute  03_analises.sql  no PostgreSQL")
