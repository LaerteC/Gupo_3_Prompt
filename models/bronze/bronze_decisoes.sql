-- grão: 1 linha = 1 linha do arquivo decisoes.csv, exatamente como chegou
-- (tudo texto, com os defeitos e duplicados). Nenhum tratamento aqui.
select * from {{ source('raw', 'decisoes') }}
