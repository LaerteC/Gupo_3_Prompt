-- grão: 1 linha = 1 decisão REJEITADA, com o motivo.
-- Fica guardada (não some) para alguém corrigir na origem.
select *
from {{ ref('silver_decisoes_tratadas') }}
where motivo_invalido is not null
