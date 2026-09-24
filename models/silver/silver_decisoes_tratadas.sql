-- grão: 1 linha = 1 decisão ÚNICA, limpa e tipada, com a coluna "motivo_invalido"
-- dizendo se ela tem algum problema. Daqui saem silver_decisoes e a quarentena.

with sem_duplicados as (
    -- defeito I3: a mesma decisão veio 2 vezes. Ficamos com 1 cópia por _id.
    select *
    from {{ ref('bronze_decisoes') }}
    qualify row_number() over (partition by trim("_id") order by _ingerido_em) = 1
),

limpo as (
    select
        trim("_id")                                              as id_documento,
        try_cast(CodDoc as bigint)                               as cod_doc,
        trim(NumProcCnj)                                         as processo_cnj,

        -- defeito R1 (real): a mesma classe aparece com e sem acento
        -- ("RECLAMAÇÃO" x "RECLAMACAO"). Defeito I1: minúsculas e espaços.
        -- Tiramos acento, espaços repetidos e padronizamos em maiúsculo.
        nullif(upper(strip_accents(regexp_replace(trim(Classe), '\s+', ' ', 'g'))), '')
                                                                 as classe,

        -- "Acórdão" = decisão do colegiado (3 desembargadores).
        -- "Decisão monocrática" = decisão de 1 desembargador sozinho.
        case upper(strip_accents(trim(DescrTipDoc)))
            when 'ACORDAO'             then 'ACORDAO'
            when 'DECISAO MONOCRATICA' then 'MONOCRATICA'
        end                                                      as tipo_decisao,

        -- defeito R2 (real): a data vem como texto "/Date(1737428400000)/",
        -- que são milissegundos desde 1970 em UTC. Tiramos o número, viramos data e
        -- passamos para o horário de Brasília (UTC-3).
        -- O valor -62135589600000 é o "ano 1" (data vazia do sistema): vira nulo.
        -- (DtHrPubl foi ignorada: em 100% das linhas ela é essa data vazia -> defeito R3)
        case
            when try_cast(regexp_extract(DtHrMov, '-?[0-9]+') as bigint) > 0
            then (epoch_ms(try_cast(regexp_extract(DtHrMov, '-?[0-9]+') as bigint))
                  - interval 3 hour)::date
        end                                                      as data_movimento,

        -- defeito R4 (real): nomes de órgão com e sem acento, com espaço duplo
        -- ("24ª CÂMARA  CÍVEL") e CORTADOS no meio ("...(ANTIGA 6ª CÂMA").
        upper(strip_accents(regexp_replace(trim(NomeOrgJulg), '\s+', ' ', 'g')))
                                                                 as orgao_original,
        try_cast(CodMagRel as integer)                           as cod_relator
    from sem_duplicados
),

com_camara as (
    select
        l.*,
        -- tira o "(ANTIGA ...)" do final, mesmo quando o nome veio cortado
        case when l.orgao_original like '%CAMARA DE DIREITO PUBLICO%'
               or l.orgao_original like '%CAMARA DE DIREITO PRIVADO%'
             then trim(regexp_replace(l.orgao_original, '\s*\(.*$', ''))
        end                                                      as camara_nova
    from limpo l
)

select
    c.id_documento, c.cod_doc, c.processo_cnj, c.classe,
    -- DECISÃO (DECISOES.md, item 3 - o dado ambíguo): "APELACAO / REMESSA NECESSARIA"
    -- conta como APELACAO, porque houve recurso da parte.
    case
        when c.classe like 'APELA%'                                   then 'APELACAO'
        when c.classe = 'AGRAVO DE INSTRUMENTO'                       then 'AGRAVO DE INSTRUMENTO'
        when c.classe like 'AGRAVO%'                                  then 'OUTROS AGRAVOS'
        when c.classe in ('REMESSA NECESSARIA', 'REEXAME NECESSARIO') then 'REMESSA NECESSARIA'
        else 'OUTRAS CLASSES'
    end                                                          as grupo_classe,
    c.tipo_decisao,
    c.data_movimento,
    c.orgao_original,
    -- DECISÃO (DECISOES.md, item 3): câmara com NOME ANTIGO ("DECIMA SEGUNDA CAMARA CIVEL")
    -- é trocada pela câmara que a SUCEDEU, pelo de-para (fonte 2).
    -- Cuidado: a antiga 12ª Cível virou a SÉTIMA de Direito Privado, e não a Décima Segunda!
    coalesce(novo.camara, antigo.camara, c.orgao_original)       as orgao_julgador,
    coalesce(
        novo.area,
        antigo.area,
        case
            when c.orgao_original like '%CRIMINAL%'        then 'CRIMINAL'
            when c.orgao_original like '%DIREITO PUBLICO%' then 'PUBLICO'
            when c.orgao_original like '%DIREITO PRIVADO%' then 'PRIVADO'
            else 'OUTROS'   -- Órgão Especial, Seção Cível, Núcleo Digital
        end
    )                                                            as area,
    (antigo.camara is not null)                                  as veio_de_nome_antigo,
    c.cod_relator,
    -- DECISÃO (DECISOES.md, item 4): registro inválido NÃO é apagado.
    -- Vai para a quarentena com o motivo escrito.
    case
        when c.data_movimento is null                    then 'DATA_MOVIMENTO_INVALIDA'   -- defeito I2
        when c.tipo_decisao is null                      then 'TIPO_DECISAO_DESCONHECIDO'
        when c.classe is null                            then 'CLASSE_VAZIA'
        when c.camara_nova is not null and novo.camara is null
                                                         then 'CAMARA_FORA_DO_DEPARA'
    end                                                          as motivo_invalido
from com_camara c
left join {{ ref('silver_camaras') }} novo   on c.camara_nova    = novo.camara
left join {{ ref('silver_camaras') }} antigo on c.orgao_original = antigo.nome_antigo
