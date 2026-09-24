-- A RESPOSTA PRINCIPAL: "Qual área do TJRJ mais decide de forma monocrática?"
-- Lê SÓ a camada de consumo (gold). ZERO regra de negócio: não há WHERE.
-- Todas as decisões (o que é válido, qual é a área) já foram tomadas no dbt.
select
    area,
    count(*)                                      as decisoes,
    sum(flag_monocratica)::int                    as monocraticas,
    round(100.0 * avg(flag_monocratica), 1)       as pct_monocratica   -- métrica derivada
from gold.gold_decisoes
group by area
order by pct_monocratica desc
