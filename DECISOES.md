# DECISÕES DO PROJETO

## A pergunta que o projeto responde

**Quais áreas e câmaras do TJRJ mais decidem sozinhas (monocraticamente, com só 1 desembargador),
por tipo de recurso e por mês?**

Essa porcentagem não existe pronta em nenhuma fonte — é calculada por nós, no gold.

## As duas fontes

| Fonte | Formato | O que é |
|---|---|---|
| `data/raw/decisoes.csv` | CSV | ~61 mil decisões do TJRJ, baixadas da Hugging Face (`celsowm/jurisprudencias_tjrj`) |
| `data/raw/camaras_depara.json` | JSON | Tabela que traduz o nome antigo de cada câmara cível para o nome novo dela |

Colunas de texto longo (ementa, teor da decisão) e o nome do relator foram deixados de fora do
download de propósito — deixariam o arquivo enorme e podem conter dado pessoal.

## Defeitos que os dados têm

**Defeitos reais**, que já vinham nos dados: classe escrita com e sem acento, datas num formato
estranho (`/Date(1737428400000)/`), e nomes de câmara com dois formatos diferentes (o antigo e o
novo). Todos tratados no dbt.

**Defeitos que nós colocamos de propósito** (para provar que o pipeline trata bem qualquer defeito):
1% das classes em minúsculo, 0,5% das datas em branco, e 0,5% das decisões duplicadas.

Os testes do dbt provam que nenhum desses defeitos chega até a camada final (`gold`).

## Decisão 1 — Por que Delta Lake + DuckDB, e nessa ordem

O dado passa por 5 camadas: **Delta Lake** (preserva o arquivo bruto, com versões) → **raw** no
DuckDB → **bronze** → **silver** (limpeza) → **gold** (resposta).

- **Por que preservar no Delta antes de tudo?** Para nunca perder o arquivo original, mesmo com
  defeito. Cada vez que o arquivo muda, vira uma versão nova — dá pra "voltar no tempo" e ver como
  os dados estavam antes.
- **Por que o banco é sempre carregado a partir do Delta, e nunca direto do arquivo?** Assim, se
  precisar reconstruir tudo do zero, o Delta garante que o resultado vai ser sempre o mesmo.
- **Por que DuckDB, e não um banco como o PostgreSQL?** Porque o DuckDB é só um arquivo — não
  precisa instalar servidor nem configurar senha. Isso deixa o projeto fácil de rodar em qualquer
  computador, sem ajuste manual.

## Decisão 2 — O que é uma linha da tabela final (o "grão")

Na tabela final (`gold.gold_decisoes`), **cada linha é uma decisão válida do TJRJ** — já com a
câmara corrigida, a área, o tipo de recurso, o mês e se foi monocrática ou não.

Ficam de fora dessa tabela: as decisões inválidas (que foram para a quarentena) e os textos longos.

Optamos por uma tabela só (não várias tabelas ligadas) porque a pergunta é uma só, com poucas
informações (área, câmara, classe, mês) — não precisa de uma estrutura mais complicada.

## Decisão 3 — O problema da câmara com dois nomes

O TJRJ reorganizou as câmaras cíveis antigas em câmaras novas (de Direito Público e Direito
Privado). Só que ~2.600 decisões no dataset ainda usam o **nome antigo** da câmara.

O cuidado que tomamos: a tradução do nome antigo para o novo **não é direta**. Por exemplo, a
antiga 12ª Câmara Cível não virou a "Décima Segunda" nova — ela virou a **Sétima** de Direito
Privado. Se a gente comparasse só o número, 128 decisões cairiam na câmara errada.

**O que fizemos:** usamos a tabela de tradução (a segunda fonte) para trocar o nome antigo pelo
nome novo certo, e marcamos essas decisões com uma coluna (`veio_de_nome_antigo`), para ficar
visível que houve essa troca.

**O que ainda fica em aberto:** uma decisão tomada pela câmara antiga, antes da reforma, deveria
"pertencer" à área da câmara que a sucedeu? Decidimos que sim — mas quem deveria confirmar isso de
verdade é o próprio tribunal (a área de estatística), que sabe se aquela câmara antiga já julgava
só matéria pública ou privada.

## Decisão 4 — O que fazer com uma decisão que tem problema

Uma decisão com algo que não dá pra confiar (data em branco, tipo de decisão desconhecido, classe
vazia, câmara sem tradução) **não é apagada**. Ela vai para uma tabela separada, a **quarentena**,
com uma coluna dizendo qual foi o motivo.

**Por que não simplesmente apagar?** Porque isso esconderia o problema — ninguém saberia que a
exportação tem falhas.

**Por que não preencher com "não informado"?** Porque, por exemplo, sem uma data, a decisão não
entra na contagem por mês — o "não informado" só empurraria o problema pra frente.

**Por que quarentena?** Porque tira a decisão problemática da resposta final, mas guarda o motivo,
para alguém corrigir na origem depois.
