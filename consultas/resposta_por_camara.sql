-- Ângulo 1: "Quais CÂMARAS mais decidem monocraticamente?"
-- Sem WHERE: só lê a camada gold.
select
    orgao_julgador,
    area,
    count(*)                                      as decisoes,
    round(100.0 * avg(flag_monocratica), 1)       as pct_monocratica
from gold.gold_decisoes
group by orgao_julgador, area
order by pct_monocratica desc, decisoes desc
