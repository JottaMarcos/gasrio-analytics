-- ============================================================
-- DISTRIBUIDORA DE GÁS RJ — ANÁLISES & GARGALOS
-- Execute no banco: distribuidora_gas
-- ============================================================

-- ============================================================
-- A1. TAXA DE ENTREGA NO PRAZO POR FILIAL
--     Gargalo: filiais abaixo de 85% indicam problema logístico
-- ============================================================
SELECT
    f.nome                                                  AS filial,
    f.zona,
    COUNT(*)                                                AS total_pedidos,
    SUM(CASE WHEN p.status = 'entregue' THEN 1 ELSE 0 END) AS entregues,
    SUM(CASE WHEN p.status = 'cancelado' THEN 1 ELSE 0 END) AS cancelados,
    SUM(CASE
        WHEN p.status = 'entregue'
         AND p.data_entrega_real <= p.data_entrega_prevista THEN 1 ELSE 0
    END)                                                    AS no_prazo,
    ROUND(
        SUM(CASE
            WHEN p.status = 'entregue'
             AND p.data_entrega_real <= p.data_entrega_prevista THEN 1 ELSE 0
        END)::NUMERIC /
        NULLIF(SUM(CASE WHEN p.status = 'entregue' THEN 1 ELSE 0 END), 0) * 100, 2
    )                                                       AS pct_no_prazo,
    ROUND(
        SUM(CASE WHEN p.status = 'cancelado' THEN 1 ELSE 0 END)::NUMERIC /
        NULLIF(COUNT(*), 0) * 100, 2
    )                                                       AS pct_cancelamento
FROM pedidos p
JOIN filiais f ON f.id_filial = p.id_filial
GROUP BY f.id_filial, f.nome, f.zona
ORDER BY pct_no_prazo ASC;


-- ============================================================
-- A2. ATRASO MÉDIO DE ENTREGA POR FILIAL (em minutos)
--     Gargalo: atraso médio > 60 min é crítico
-- ============================================================
SELECT
    f.nome                          AS filial,
    COUNT(*)                        AS entregas_com_atraso,
    ROUND(AVG(
        EXTRACT(EPOCH FROM (p.data_entrega_real - p.data_entrega_prevista)) / 60
    ), 1)                           AS atraso_medio_minutos,
    MAX(
        EXTRACT(EPOCH FROM (p.data_entrega_real - p.data_entrega_prevista)) / 60
    )::INT                          AS atraso_maximo_minutos
FROM pedidos p
JOIN filiais f ON f.id_filial = p.id_filial
WHERE p.status = 'entregue'
  AND p.data_entrega_real > p.data_entrega_prevista
GROUP BY f.id_filial, f.nome
ORDER BY atraso_medio_minutos DESC;


-- ============================================================
-- A3. INADIMPLÊNCIA POR FILIAL
--     Gargalo: valor em aberto/vencido alto por filial
-- ============================================================
SELECT
    f.nome                                              AS filial,
    COUNT(DISTINCT cr.id_cliente)                       AS clientes_devedores,
    COUNT(cr.id_conta)                                  AS total_contas,
    SUM(cr.valor + cr.juros)                            AS valor_total_divida,
    SUM(CASE WHEN cr.status = 'vencido' THEN cr.valor + cr.juros ELSE 0 END)  AS valor_vencido,
    SUM(CASE WHEN cr.status = 'aberto'  THEN cr.valor ELSE 0 END)              AS valor_em_aberto,
    SUM(CASE WHEN cr.status = 'renegociado' THEN cr.valor ELSE 0 END)          AS valor_renegociado,
    ROUND(
        SUM(CASE WHEN cr.status IN ('vencido','aberto') THEN cr.valor ELSE 0 END)::NUMERIC /
        NULLIF(SUM(cr.valor), 0) * 100, 2
    )                                                   AS pct_inadimplencia
FROM contas_receber cr
JOIN pedidos p  ON p.id_pedido = cr.id_pedido
JOIN filiais f  ON f.id_filial = p.id_filial
WHERE cr.status != 'pago'
GROUP BY f.id_filial, f.nome
ORDER BY valor_vencido DESC;


-- ============================================================
-- A4. CUSTO DE MANUTENÇÃO vs PRODUTIVIDADE DOS VEÍCULOS
--     Gargalo: veículos com alto custo e baixa entrega
-- ============================================================
SELECT
    v.placa,
    v.modelo,
    f.nome                                          AS filial,
    v.km_atual,
    COUNT(DISTINCT p.id_pedido)                     AS pedidos_realizados,
    COALESCE(SUM(mv.custo), 0)                      AS custo_total_manutencao,
    COUNT(mv.id_manutencao)                         AS qtd_manutencoes,
    ROUND(COALESCE(SUM(mv.custo),0) /
          NULLIF(COUNT(DISTINCT p.id_pedido),0), 2) AS custo_por_pedido,
    v.status
FROM veiculos v
LEFT JOIN manutencoes_veiculos mv ON mv.id_veiculo = v.id_veiculo
LEFT JOIN pedidos p ON p.id_veiculo = v.id_veiculo AND p.status = 'entregue'
JOIN filiais f ON f.id_filial = v.id_filial
GROUP BY v.id_veiculo, v.placa, v.modelo, f.nome, v.km_atual, v.status
ORDER BY custo_total_manutencao DESC
LIMIT 20;


-- ============================================================
-- A5. ESTOQUE CRÍTICO (abaixo do mínimo)
--     Gargalo: risco de ruptura de estoque
-- ============================================================
SELECT
    f.nome                                              AS filial,
    pr.descricao                                        AS produto,
    pr.tipo,
    e.quantidade                                        AS estoque_atual,
    e.estoque_minimo,
    e.quantidade - e.estoque_minimo                     AS diferenca,
    ROUND(e.quantidade::NUMERIC / e.estoque_minimo * 100, 1) AS pct_do_minimo,
    CASE
        WHEN e.quantidade = 0               THEN '🔴 SEM ESTOQUE'
        WHEN e.quantidade < e.estoque_minimo THEN '🟡 ABAIXO DO MÍNIMO'
        ELSE '🟢 OK'
    END                                                 AS situacao
FROM estoque e
JOIN filiais f   ON f.id_filial   = e.id_filial
JOIN produtos pr ON pr.id_produto = e.id_produto
WHERE e.quantidade <= e.estoque_minimo
ORDER BY pct_do_minimo ASC, f.nome;


-- ============================================================
-- A6. MOTIVOS DE CANCELAMENTO
--     Gargalo: identificar causa raiz dos cancelamentos
-- ============================================================
SELECT
    motivo_cancelamento,
    COUNT(*)                                        AS total,
    ROUND(COUNT(*)::NUMERIC /
          SUM(COUNT(*)) OVER() * 100, 2)            AS pct_total,
    f.nome                                          AS filial_maior_incidencia
FROM pedidos p
JOIN filiais f ON f.id_filial = p.id_filial
WHERE p.status = 'cancelado'
  AND p.motivo_cancelamento IS NOT NULL
GROUP BY motivo_cancelamento, f.nome
ORDER BY total DESC;


-- ============================================================
-- A7. RANKING DE CLIENTES (RFM simplificado)
--     Recência, Frequência e Valor Monetário
-- ============================================================
SELECT
    c.nome,
    c.tipo,
    c.bairro,
    f.nome                                              AS filial_atendimento,
    COUNT(p.id_pedido)                                  AS total_pedidos,
    SUM(p.valor_final)                                  AS valor_total_gasto,
    ROUND(AVG(p.valor_final), 2)                        AS ticket_medio,
    MAX(p.data_pedido)::DATE                            AS ultimo_pedido,
    DATE_PART('day', NOW() - MAX(p.data_pedido))::INT   AS dias_sem_compra,
    CASE
        WHEN DATE_PART('day', NOW() - MAX(p.data_pedido)) <= 30  THEN 'ATIVO'
        WHEN DATE_PART('day', NOW() - MAX(p.data_pedido)) <= 90  THEN 'RISCO'
        ELSE 'INATIVO'
    END                                                 AS situacao_cliente
FROM clientes c
JOIN pedidos p  ON p.id_cliente = c.id_cliente AND p.status = 'entregue'
JOIN filiais f  ON f.id_filial  = c.id_filial_atend
GROUP BY c.id_cliente, c.nome, c.tipo, c.bairro, f.nome
HAVING COUNT(p.id_pedido) >= 3
ORDER BY valor_total_gasto DESC
LIMIT 30;


-- ============================================================
-- A8. DESEMPENHO DE ENTREGADORES
--     Gargalo: entregadores com baixa nota e alta ocorrência
-- ============================================================
SELECT
    fn.nome                                         AS entregador,
    f.nome                                          AS filial,
    COUNT(DISTINCT p.id_pedido)                     AS total_entregas,
    COUNT(DISTINCT oc.id_ocorrencia)                AS total_ocorrencias,
    ROUND(AVG(av.nota), 2)                          AS nota_media,
    SUM(CASE WHEN p.data_entrega_real > p.data_entrega_prevista
             THEN 1 ELSE 0 END)                     AS entregas_atrasadas,
    ROUND(
        SUM(CASE WHEN p.data_entrega_real > p.data_entrega_prevista
                 THEN 1 ELSE 0 END)::NUMERIC /
        NULLIF(COUNT(DISTINCT p.id_pedido),0) * 100, 2
    )                                               AS pct_atraso
FROM funcionarios fn
JOIN filiais f    ON f.id_filial   = fn.id_filial
JOIN pedidos p    ON p.id_entregador = fn.id_funcionario AND p.status = 'entregue'
LEFT JOIN ocorrencias oc ON oc.id_funcionario = fn.id_funcionario
LEFT JOIN avaliacoes av  ON av.id_pedido = p.id_pedido
WHERE fn.cargo = 'entregador'
GROUP BY fn.id_funcionario, fn.nome, f.nome
HAVING COUNT(DISTINCT p.id_pedido) >= 10
ORDER BY nota_media ASC, pct_atraso DESC;


-- ============================================================
-- A9. FATURAMENTO MENSAL POR FILIAL (últimos 24 meses)
-- ============================================================
SELECT
    f.nome                                          AS filial,
    DATE_TRUNC('month', p.data_pedido)::DATE        AS mes,
    COUNT(*)                                        AS total_pedidos,
    SUM(p.valor_final)                              AS faturamento,
    ROUND(AVG(p.valor_final), 2)                    AS ticket_medio,
    SUM(p.desconto)                                 AS total_descontos
FROM pedidos p
JOIN filiais f ON f.id_filial = p.id_filial
WHERE p.status = 'entregue'
  AND p.data_pedido >= NOW() - INTERVAL '24 months'
GROUP BY f.id_filial, f.nome, DATE_TRUNC('month', p.data_pedido)
ORDER BY f.nome, mes;


-- ============================================================
-- A10. CANAL DE VENDA MAIS LUCRATIVO
-- ============================================================
SELECT
    p.canal,
    COUNT(*)                                        AS total_pedidos,
    ROUND(COUNT(*)::NUMERIC /
          SUM(COUNT(*)) OVER() * 100, 2)            AS pct_pedidos,
    SUM(p.valor_final)                              AS faturamento_total,
    ROUND(AVG(p.valor_final), 2)                    AS ticket_medio,
    SUM(CASE WHEN p.status = 'cancelado' THEN 1 ELSE 0 END) AS cancelamentos,
    ROUND(
        SUM(CASE WHEN p.status = 'cancelado' THEN 1 ELSE 0 END)::NUMERIC /
        NULLIF(COUNT(*),0) * 100, 2
    )                                               AS pct_cancelamento
FROM pedidos p
GROUP BY p.canal
ORDER BY faturamento_total DESC;


-- ============================================================
-- A11. PRODUTO MAIS VENDIDO POR FILIAL
-- ============================================================
SELECT
    f.nome          AS filial,
    pr.descricao    AS produto,
    pr.tipo,
    SUM(ip.quantidade)      AS qtd_vendida,
    SUM(ip.subtotal)        AS receita_total,
    RANK() OVER (
        PARTITION BY f.id_filial
        ORDER BY SUM(ip.quantidade) DESC
    )               AS ranking
FROM itens_pedido ip
JOIN pedidos p  ON p.id_pedido  = ip.id_pedido AND p.status = 'entregue'
JOIN filiais f  ON f.id_filial  = p.id_filial
JOIN produtos pr ON pr.id_produto = ip.id_produto
GROUP BY f.id_filial, f.nome, pr.id_produto, pr.descricao, pr.tipo
HAVING RANK() OVER (
    PARTITION BY f.id_filial ORDER BY SUM(ip.quantidade) DESC
) <= 3
ORDER BY f.nome, ranking;


-- ============================================================
-- A12. OCORRÊNCIAS POR TIPO E CUSTO TOTAL
--      Gargalo: tipos de ocorrência que mais custam
-- ============================================================
SELECT
    tipo,
    gravidade,
    COUNT(*)                        AS total,
    SUM(custo_ocorrencia)           AS custo_total,
    ROUND(AVG(custo_ocorrencia),2)  AS custo_medio,
    SUM(CASE WHEN status = 'aberto' THEN 1 ELSE 0 END) AS pendentes,
    SUM(CASE WHEN notificado_orgao THEN 1 ELSE 0 END)   AS notificados_inmetro
FROM ocorrencias
GROUP BY tipo, gravidade
ORDER BY custo_total DESC;


-- ============================================================
-- A13. KPI EXECUTIVO CONSOLIDADO (SNAPSHOT ATUAL)
-- ============================================================
SELECT
    'Total de Clientes Ativos'      AS indicador,
    COUNT(*)::TEXT                  AS valor
FROM clientes WHERE ativo = TRUE

UNION ALL SELECT
    'Pedidos Entregues (total)',
    COUNT(*)::TEXT FROM pedidos WHERE status = 'entregue'

UNION ALL SELECT
    'Pedidos Cancelados (total)',
    COUNT(*)::TEXT FROM pedidos WHERE status = 'cancelado'

UNION ALL SELECT
    'Taxa de Cancelamento (%)',
    ROUND(
        COUNT(*) FILTER (WHERE status = 'cancelado')::NUMERIC /
        NULLIF(COUNT(*), 0) * 100, 2
    )::TEXT || '%'
FROM pedidos

UNION ALL SELECT
    'Faturamento Total (R$)',
    'R$ ' || TO_CHAR(SUM(valor_final),'FM999,999,999.00')
FROM pedidos WHERE status = 'entregue'

UNION ALL SELECT
    'Ticket Médio (R$)',
    'R$ ' || TO_CHAR(AVG(valor_final),'FM999,999.00')
FROM pedidos WHERE status = 'entregue'

UNION ALL SELECT
    'Valor Inadimplente (R$)',
    'R$ ' || TO_CHAR(SUM(valor + juros),'FM999,999.00')
FROM contas_receber WHERE status IN ('vencido','aberto')

UNION ALL SELECT
    'Ocorrências Críticas Abertas',
    COUNT(*)::TEXT
FROM ocorrencias WHERE gravidade = 'critica' AND status != 'resolvido'

UNION ALL SELECT
    'Botijões Não Devolvidos',
    COUNT(*)::TEXT
FROM botijoes_clientes WHERE status = 'com_cliente'

UNION ALL SELECT
    'Nota Média de Satisfação',
    ROUND(AVG(nota), 2)::TEXT || '/10'
FROM avaliacoes;
