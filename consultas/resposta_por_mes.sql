-- Ângulo 3: o % de decisões monocráticas MÊS a MÊS, por área.
select
    mes,
    area,
    count(*)                                      as decisoes,
    round(100.0 * avg(flag_monocratica), 1)       as pct_monocratica
from gold.gold_decisoes
group by mes, area
order by mes, area desc
