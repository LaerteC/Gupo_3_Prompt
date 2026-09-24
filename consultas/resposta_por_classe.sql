-- Ângulo 2: o % de decisões monocráticas por TIPO DE RECURSO em cada área.
select
    grupo_classe,
    area,
    count(*)                                      as decisoes,
    round(100.0 * avg(flag_monocratica), 1)       as pct_monocratica
from gold.gold_decisoes
group by grupo_classe, area
order by grupo_classe, pct_monocratica desc
