-- grão: 1 linha = 1 câmara cível ATUAL (Direito Público ou Privado)
select
    -- sem acento e em maiúsculo: "SÉTIMA CÂMARA DE DIREITO PÚBLICO" e
    -- "SETIMA CAMARA DE DIREITO PUBLICO" passam a ser o mesmo texto
    upper(strip_accents(trim(camara_atual)))            as camara,
    upper(trim(area))                                   as area,
    try_cast(antiga_camara_civel as integer)            as antiga_numero,
    -- nome como a câmara aparecia ANTES da reestruturação (ex.: "DECIMA SEGUNDA CAMARA CIVEL")
    upper(strip_accents(trim(nome_antigo)))             as nome_antigo
from {{ ref('bronze_camaras') }}
