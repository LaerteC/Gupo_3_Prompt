-- grão: 1 linha = 1 câmara do arquivo camaras_depara.json, como chegou (tudo texto)
select * from {{ source('raw', 'camaras') }}
