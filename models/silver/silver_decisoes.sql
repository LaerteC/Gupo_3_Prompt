-- grão: 1 linha = 1 decisão válida (limpa, tipada, sem duplicados)
select * exclude (motivo_invalido)
from {{ ref('silver_decisoes_tratadas') }}
where motivo_invalido is null
