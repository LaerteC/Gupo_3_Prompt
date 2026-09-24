-- ============================================================================
-- GRÃO: 1 linha = 1 DECISÃO válida do TJRJ (acórdão ou decisão monocrática).
-- Pergunta de negócio: "Quais áreas e câmaras do TJRJ mais decidem de forma
--                       MONOCRÁTICA (1 desembargador sozinho), por tipo de
--                       recurso e ao longo dos meses?"
-- Formato: TABELA LARGA (tudo numa tabela só) -> ver DECISOES.md, item 2.
-- Fica de fora: as decisões da quarentena e as colunas de texto (ementa, tese).
-- ============================================================================
select
    id_documento,
    processo_cnj,
    data_movimento,
    strftime(data_movimento, '%Y-%m')                       as mes,
    orgao_julgador,
    area,
    veio_de_nome_antigo,
    classe,
    grupo_classe,
    tipo_decisao,
    -- MÉTRICA DERIVADA (não existe em nenhuma fonte):
    -- 1 = decidida monocraticamente, 0 = decidida pelo colegiado.
    -- A média desta coluna vira o "% de decisões monocráticas".
    case when tipo_decisao = 'MONOCRATICA' then 1 else 0 end as flag_monocratica,
    cod_relator
from {{ ref('silver_decisoes') }}
