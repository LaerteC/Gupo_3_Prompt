-- Teste "singular" (escrito à mão): toda câmara com NOME ANTIGO ("... CAMARA CIVEL")
-- tem que ter sido trocada pela câmara nova. Se sobrar alguma, o de-para está incompleto.
-- O teste passa quando esta consulta volta VAZIA.
select orgao_julgador, count(*) as decisoes
from {{ ref('silver_decisoes') }}
where orgao_julgador like '%CAMARA CIVEL'
group by orgao_julgador
