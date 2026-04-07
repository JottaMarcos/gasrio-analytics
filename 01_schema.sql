-- ============================================================
-- DISTRIBUIDORA DE GÁS RJ — SCHEMA COMPLETO
-- Banco: distribuidora_gas
-- Autor: Projeto Analítico
-- ============================================================

-- Criar banco (rodar separado no psql se necessário):
-- CREATE DATABASE distribuidora_gas;
-- \c distribuidora_gas

-- ============================================================
-- 1. FILIAIS
-- ============================================================
CREATE TABLE IF NOT EXISTS filiais (
    id_filial       SERIAL PRIMARY KEY,
    nome            VARCHAR(100) NOT NULL,
    bairro          VARCHAR(100) NOT NULL,
    zona            VARCHAR(50)  NOT NULL,
    endereco        VARCHAR(200) NOT NULL,
    cep             VARCHAR(10)  NOT NULL,
    telefone        VARCHAR(20),
    cnpj            VARCHAR(20)  UNIQUE NOT NULL,
    gerente         VARCHAR(100),
    capacidade_max  INTEGER NOT NULL,  -- máx botijões em estoque
    ativa           BOOLEAN DEFAULT TRUE,
    data_abertura   DATE
);

-- ============================================================
-- 2. FUNCIONÁRIOS
-- ============================================================
CREATE TABLE IF NOT EXISTS funcionarios (
    id_funcionario  SERIAL PRIMARY KEY,
    id_filial       INTEGER REFERENCES filiais(id_filial),
    nome            VARCHAR(100) NOT NULL,
    cpf             VARCHAR(14)  UNIQUE NOT NULL,
    cargo           VARCHAR(50)  NOT NULL,  -- entregador, atendente, gerente, técnico, supervisor
    salario         NUMERIC(10,2) NOT NULL,
    comissao_pct    NUMERIC(5,2) DEFAULT 0, -- % comissão sobre vendas/entregas
    data_admissao   DATE NOT NULL,
    data_demissao   DATE,
    ativo           BOOLEAN DEFAULT TRUE,
    cnh             VARCHAR(20),
    telefone        VARCHAR(20)
);

-- ============================================================
-- 3. VEÍCULOS (FROTA)
-- ============================================================
CREATE TABLE IF NOT EXISTS veiculos (
    id_veiculo      SERIAL PRIMARY KEY,
    id_filial       INTEGER REFERENCES filiais(id_filial),
    placa           VARCHAR(10)  UNIQUE NOT NULL,
    modelo          VARCHAR(100) NOT NULL,
    marca           VARCHAR(50)  NOT NULL,
    ano             INTEGER,
    capacidade_botijoes INTEGER NOT NULL,
    km_atual        INTEGER DEFAULT 0,
    status          VARCHAR(30) DEFAULT 'disponivel', -- disponivel, em_rota, manutencao, inativo
    data_aquisicao  DATE,
    ultimo_abastecimento DATE
);

-- ============================================================
-- 4. MANUTENÇÃO DE VEÍCULOS
-- ============================================================
CREATE TABLE IF NOT EXISTS manutencoes_veiculos (
    id_manutencao   SERIAL PRIMARY KEY,
    id_veiculo      INTEGER REFERENCES veiculos(id_veiculo),
    tipo            VARCHAR(50) NOT NULL, -- preventiva, corretiva, revisao
    descricao       TEXT,
    custo           NUMERIC(10,2),
    km_na_manutencao INTEGER,
    data_entrada    DATE NOT NULL,
    data_saida      DATE,
    oficina         VARCHAR(100),
    status          VARCHAR(20) DEFAULT 'concluida' -- agendada, em_andamento, concluida
);

-- ============================================================
-- 5. FORNECEDORES
-- ============================================================
CREATE TABLE IF NOT EXISTS fornecedores (
    id_fornecedor   SERIAL PRIMARY KEY,
    razao_social    VARCHAR(150) NOT NULL,
    cnpj            VARCHAR(20)  UNIQUE NOT NULL,
    contato         VARCHAR(100),
    telefone        VARCHAR(20),
    email           VARCHAR(100),
    prazo_entrega_dias INTEGER DEFAULT 3,
    avaliacao       NUMERIC(3,1) CHECK (avaliacao BETWEEN 1 AND 5),
    ativo           BOOLEAN DEFAULT TRUE
);

-- ============================================================
-- 6. PRODUTOS
-- ============================================================
CREATE TABLE IF NOT EXISTS produtos (
    id_produto      SERIAL PRIMARY KEY,
    codigo          VARCHAR(20) UNIQUE NOT NULL,
    descricao       VARCHAR(150) NOT NULL,
    tipo            VARCHAR(30) NOT NULL, -- botijao_p13, botijao_p45, botijao_p190, granel, acessorio
    peso_kg         NUMERIC(8,2),
    preco_custo     NUMERIC(10,2) NOT NULL,
    preco_venda     NUMERIC(10,2) NOT NULL,
    unidade         VARCHAR(20) DEFAULT 'unidade',
    ativo           BOOLEAN DEFAULT TRUE
);

-- ============================================================
-- 7. ESTOQUE POR FILIAL
-- ============================================================
CREATE TABLE IF NOT EXISTS estoque (
    id_estoque      SERIAL PRIMARY KEY,
    id_filial       INTEGER REFERENCES filiais(id_filial),
    id_produto      INTEGER REFERENCES produtos(id_produto),
    quantidade      INTEGER NOT NULL DEFAULT 0,
    estoque_minimo  INTEGER NOT NULL DEFAULT 10,
    estoque_maximo  INTEGER NOT NULL DEFAULT 500,
    ultima_atualizacao TIMESTAMP DEFAULT NOW(),
    UNIQUE (id_filial, id_produto)
);

-- ============================================================
-- 8. MOVIMENTAÇÕES DE ESTOQUE
-- ============================================================
CREATE TABLE IF NOT EXISTS movimentacoes_estoque (
    id_movimentacao SERIAL PRIMARY KEY,
    id_filial       INTEGER REFERENCES filiais(id_filial),
    id_produto      INTEGER REFERENCES produtos(id_produto),
    tipo            VARCHAR(20) NOT NULL, -- entrada, saida, ajuste, transferencia
    quantidade      INTEGER NOT NULL,
    motivo          VARCHAR(100), -- venda, compra, devolucao, perda, transferencia_entre_filiais
    id_referencia   INTEGER,     -- id do pedido ou compra relacionada
    data_movimentacao TIMESTAMP DEFAULT NOW(),
    id_funcionario  INTEGER REFERENCES funcionarios(id_funcionario)
);

-- ============================================================
-- 9. COMPRAS DE FORNECEDOR
-- ============================================================
CREATE TABLE IF NOT EXISTS compras (
    id_compra       SERIAL PRIMARY KEY,
    id_filial       INTEGER REFERENCES filiais(id_filial),
    id_fornecedor   INTEGER REFERENCES fornecedores(id_fornecedor),
    data_pedido     DATE NOT NULL,
    data_entrega_prevista DATE,
    data_entrega_real DATE,
    status          VARCHAR(30) DEFAULT 'pendente', -- pendente, confirmado, entregue, cancelado, atrasado
    valor_total     NUMERIC(12,2),
    observacao      TEXT
);

CREATE TABLE IF NOT EXISTS itens_compra (
    id_item         SERIAL PRIMARY KEY,
    id_compra       INTEGER REFERENCES compras(id_compra),
    id_produto      INTEGER REFERENCES produtos(id_produto),
    quantidade      INTEGER NOT NULL,
    preco_unitario  NUMERIC(10,2) NOT NULL,
    subtotal        NUMERIC(12,2) GENERATED ALWAYS AS (quantidade * preco_unitario) STORED
);

-- ============================================================
-- 10. CLIENTES
-- ============================================================
CREATE TABLE IF NOT EXISTS clientes (
    id_cliente      SERIAL PRIMARY KEY,
    tipo            VARCHAR(20) NOT NULL DEFAULT 'PF', -- PF, PJ
    nome            VARCHAR(150) NOT NULL,
    cpf_cnpj        VARCHAR(20)  UNIQUE NOT NULL,
    telefone        VARCHAR(20),
    email           VARCHAR(100),
    endereco        VARCHAR(200),
    bairro          VARCHAR(100),
    zona            VARCHAR(50),
    cep             VARCHAR(10),
    id_filial_atend INTEGER REFERENCES filiais(id_filial), -- filial que atende
    data_cadastro   DATE DEFAULT CURRENT_DATE,
    ativo           BOOLEAN DEFAULT TRUE,
    permite_fiado   BOOLEAN DEFAULT FALSE,
    limite_fiado    NUMERIC(10,2) DEFAULT 0,
    canal_preferido VARCHAR(30) DEFAULT 'telefone' -- telefone, app, whatsapp, balcao
);

-- ============================================================
-- 11. PEDIDOS
-- ============================================================
CREATE TABLE IF NOT EXISTS pedidos (
    id_pedido       SERIAL PRIMARY KEY,
    id_cliente      INTEGER REFERENCES clientes(id_cliente),
    id_filial       INTEGER REFERENCES filiais(id_filial),
    id_funcionario  INTEGER REFERENCES funcionarios(id_funcionario), -- atendente
    data_pedido     TIMESTAMP DEFAULT NOW(),
    data_entrega_prevista TIMESTAMP,
    data_entrega_real TIMESTAMP,
    status          VARCHAR(30) DEFAULT 'pendente',
    -- pendente, confirmado, em_rota, entregue, cancelado, devolvido
    canal           VARCHAR(30) DEFAULT 'telefone', -- telefone, app, whatsapp, balcao
    forma_pagamento VARCHAR(30), -- dinheiro, pix, cartao_debito, cartao_credito, fiado
    valor_total     NUMERIC(10,2),
    desconto        NUMERIC(10,2) DEFAULT 0,
    valor_final     NUMERIC(10,2),
    observacao      TEXT,
    motivo_cancelamento TEXT,
    id_veiculo      INTEGER REFERENCES veiculos(id_veiculo),
    id_entregador   INTEGER REFERENCES funcionarios(id_funcionario)
);

CREATE TABLE IF NOT EXISTS itens_pedido (
    id_item         SERIAL PRIMARY KEY,
    id_pedido       INTEGER REFERENCES pedidos(id_pedido),
    id_produto      INTEGER REFERENCES produtos(id_produto),
    quantidade      INTEGER NOT NULL,
    preco_unitario  NUMERIC(10,2) NOT NULL,
    subtotal        NUMERIC(12,2) GENERATED ALWAYS AS (quantidade * preco_unitario) STORED
);

-- ============================================================
-- 12. FINANCEIRO — CONTAS A RECEBER / FIADO
-- ============================================================
CREATE TABLE IF NOT EXISTS contas_receber (
    id_conta        SERIAL PRIMARY KEY,
    id_pedido       INTEGER REFERENCES pedidos(id_pedido),
    id_cliente      INTEGER REFERENCES clientes(id_cliente),
    valor           NUMERIC(10,2) NOT NULL,
    data_vencimento DATE NOT NULL,
    data_pagamento  DATE,
    status          VARCHAR(20) DEFAULT 'aberto', -- aberto, pago, vencido, renegociado
    juros           NUMERIC(10,2) DEFAULT 0,
    observacao      TEXT
);

-- ============================================================
-- 13. OCORRÊNCIAS / INCIDENTES
-- ============================================================
CREATE TABLE IF NOT EXISTS ocorrencias (
    id_ocorrencia   SERIAL PRIMARY KEY,
    id_filial       INTEGER REFERENCES filiais(id_filial),
    id_pedido       INTEGER REFERENCES pedidos(id_pedido),
    id_cliente      INTEGER REFERENCES clientes(id_cliente),
    id_funcionario  INTEGER REFERENCES funcionarios(id_funcionario),
    tipo            VARCHAR(50) NOT NULL,
    -- vazamento, acidente, reclamacao_cliente, avaria_produto,
    -- endereco_errado, cliente_ausente, veiculo_quebrado, furto
    descricao       TEXT,
    gravidade       VARCHAR(20) DEFAULT 'baixa', -- baixa, media, alta, critica
    status          VARCHAR(20) DEFAULT 'aberto', -- aberto, em_analise, resolvido
    data_ocorrencia TIMESTAMP DEFAULT NOW(),
    data_resolucao  TIMESTAMP,
    custo_ocorrencia NUMERIC(10,2) DEFAULT 0,
    notificado_orgao BOOLEAN DEFAULT FALSE -- INMETRO, Bombeiros, etc.
);

-- ============================================================
-- 14. CONTROLE DE BOTIJÕES EMPRESTADOS
-- ============================================================
CREATE TABLE IF NOT EXISTS botijoes_clientes (
    id_registro     SERIAL PRIMARY KEY,
    id_cliente      INTEGER REFERENCES clientes(id_cliente),
    id_produto      INTEGER REFERENCES produtos(id_produto),
    quantidade      INTEGER NOT NULL DEFAULT 1,
    data_emprestimo DATE NOT NULL,
    data_devolucao  DATE,
    status          VARCHAR(20) DEFAULT 'com_cliente', -- com_cliente, devolvido, perdido
    id_pedido_origem INTEGER REFERENCES pedidos(id_pedido)
);

-- ============================================================
-- 15. PREÇOS HISTÓRICOS (variação Petrobras)
-- ============================================================
CREATE TABLE IF NOT EXISTS historico_precos (
    id_historico    SERIAL PRIMARY KEY,
    id_produto      INTEGER REFERENCES produtos(id_produto),
    preco_custo_anterior NUMERIC(10,2),
    preco_custo_novo     NUMERIC(10,2),
    preco_venda_anterior NUMERIC(10,2),
    preco_venda_novo     NUMERIC(10,2),
    data_alteracao  DATE NOT NULL,
    motivo          VARCHAR(150) -- reajuste_petrobras, concorrencia, margem, etc.
);

-- ============================================================
-- 16. MULTAS / INFRAÇÕES DE VEÍCULOS
-- ============================================================
CREATE TABLE IF NOT EXISTS multas (
    id_multa        SERIAL PRIMARY KEY,
    id_veiculo      INTEGER REFERENCES veiculos(id_veiculo),
    id_funcionario  INTEGER REFERENCES funcionarios(id_funcionario),
    data_infracao   DATE NOT NULL,
    tipo_infracao   VARCHAR(100),
    valor           NUMERIC(10,2),
    status          VARCHAR(20) DEFAULT 'pendente', -- pendente, pago, recorrido
    responsavel     VARCHAR(20) DEFAULT 'empresa'   -- empresa, funcionario
);

-- ============================================================
-- 17. AVALIAÇÕES DE ENTREGA (NPS / Satisfação)
-- ============================================================
CREATE TABLE IF NOT EXISTS avaliacoes (
    id_avaliacao    SERIAL PRIMARY KEY,
    id_pedido       INTEGER REFERENCES pedidos(id_pedido),
    id_cliente      INTEGER REFERENCES clientes(id_cliente),
    nota            INTEGER CHECK (nota BETWEEN 1 AND 10),
    comentario      TEXT,
    data_avaliacao  TIMESTAMP DEFAULT NOW(),
    canal_avaliacao VARCHAR(30) -- app, whatsapp, telefone, site
);

-- ============================================================
-- ÍNDICES PARA PERFORMANCE
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_pedidos_status     ON pedidos(status);
CREATE INDEX IF NOT EXISTS idx_pedidos_data       ON pedidos(data_pedido);
CREATE INDEX IF NOT EXISTS idx_pedidos_filial     ON pedidos(id_filial);
CREATE INDEX IF NOT EXISTS idx_pedidos_cliente    ON pedidos(id_cliente);
CREATE INDEX IF NOT EXISTS idx_clientes_filial    ON clientes(id_filial_atend);
CREATE INDEX IF NOT EXISTS idx_estoque_filial     ON estoque(id_filial);
CREATE INDEX IF NOT EXISTS idx_ocorrencias_tipo   ON ocorrencias(tipo);
CREATE INDEX IF NOT EXISTS idx_contas_status      ON contas_receber(status);
CREATE INDEX IF NOT EXISTS idx_movimentacoes_data ON movimentacoes_estoque(data_movimentacao);

-- ============================================================
-- FIM DO SCHEMA
-- ============================================================
SELECT 'Schema criado com sucesso! 17 tabelas.' AS resultado;
