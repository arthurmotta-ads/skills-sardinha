---
name: campanha-live-sci
description: Sobe no Meta Ads a campanha de inscrição de live da SCI Sistemas, no molde da live "O contador no centro da Reforma Tributária" de 11/11/2026. Recebe a pasta de criativos, o site de inscrição, o orçamento diário e as datas; renomeia os criativos no padrão AD01_SCI_<TEMA>_<FORMATO>, junta feed e vertical da mesma arte num anúncio só, escreve os textos com a copy-meta-ads e sobe 1 campanha CBO com 4 conjuntos (lista de e-mail, engajamento 30D, engajamento 365D e semelhante 2%), tudo PAUSED e com Advantage desligado. Use quando o Arthur pedir "sobe a campanha da live da SCI", "campanha de live SCI", "nova live da SCI", mandar criativos e o link de inscrição de uma live da SCI, ou rodar /campanha-live-sci.
---

# Campanha de live da SCI 🐟

Molde de origem: `clientes/sci-sistemas/moldes-meta/live-contador-centro-reforma-leads-site-11-11-26.md` (e o `.json` ao lado). A configuração fixa (conta, página, Instagram, pixel, públicos e conjuntos) fica em `config-sci.json`, nesta pasta (no repositório público vai só o modelo `config-sci.exemplo.json`; copiar para `config-sci.json` e preencher). O script `scripts/subir_live.py` cria tudo pela API usando o token da `meta-ads-ratos`.

Ler antes de começar: `~/.claude/skills/meta-ads-ratos/aprendizados.md`.

## O que já é fixo (não perguntar)

- **Campanha:** objetivo Leads, leilão, CBO com orçamento **diário**, menor custo sem limite, sem categoria especial.
- **Conjuntos (4):** otimização em conversão no site, evento CompleteRegistration do pixel da conta, atribuição de 7 dias pelo clique, 1 dia pela visualização e 1 dia por vídeo engajado. Brasil, 25 a 55 anos, todos os gêneros. Facebook, Instagram e Messenger, **sem Audience Network**. Advantage+ de público e expansão de público personalizado **desligados**.

| Conjunto | Público | Exclui |
|---|---|---|
| 00_AUTO_LISTA_EMAIL | lista de clientes (01/04/26) + não clientes (12/02/25) | nada |
| 02_AUTO_ENVOLVIMENTO_30D | engajamento IG e FB 30D | as duas listas |
| 03_AUTO_ENVOLVIMENTO_365D | engajamento IG e FB 365D | engajamento 30D e as listas |
| 03_AUTO_LOOKALIKE_2_ENVOLVIMENTO_30D | semelhante 2% do engajamento FB e IG 30D | engajamento 30D e 365D e as listas |

Os conjuntos de interesses, visitou a página e video view ficaram de fora de propósito (não performam no histórico). As listas são sempre as mesmas; atualização é manual, pelo Arthur.

- **Anúncios:** botão Saiba mais, todos os recursos do Advantage+ criativo desligados, UTMs `utm_source=meta&utm_medium=cpc&utm_campaign={{campaign.name}}&utm_id=<utm_id>&utm_term={{adset.name}}&utm_content={{ad.name}}`. Cada criativo é criado uma vez e usado nos 4 conjuntos, então vira **um post só** (curtidas e comentários somam).
- **Status:** tudo PAUSED.

## Passo 1. Coletar

Se faltar algo, pedir só o que falta, num bloco:

```
Pasta dos criativos:
Site de inscrição:
Orçamento diário:
Início da campanha:
```

O fim é a data e hora da live, lida no site. Se o Arthur der "duração" em vez de início, contar para trás a partir da live. Início padrão às 09:00 (horário de Brasília, `-0300`).

## Passo 2. Ler o site da live

Abrir a página (WebFetch, ou `firecrawl_scrape` se vier vazia). Tirar: título da live, data e hora, palestrantes e cargos, público, o que a pessoa vai aprender, formato (online, gratuito). Daí sai:

- **TEMA:** 2 ou 3 palavras em maiúsculo, sem acento, separadas por `_` (ex: `CONTADOR_REFORMA`).
- **Nome da campanha:** `LIVE_<TEMA>_LEADS_SITE_<DD>_<MM>_<AA>` com a data da live.
- **utm_id:** `live_<sigla>_<DDMMAA>`, com a sigla do assunto em minúsculo (ex: `live_rt_111126` pra Reforma Tributária).

Se a hora da live não estiver no site, perguntar.

## Passo 3. Ver os criativos e juntar os pares

```bash
ls -la "<PASTA>"
sips -g pixelWidth -g pixelHeight "<PASTA>"/*.{png,jpg,jpeg} 2>/dev/null
for f in "<PASTA>"/*.{mp4,mov}; do ffprobe -v error -select_streams v:0 -show_entries stream=width,height:format=duration -of csv=p=0 "$f"; done 2>/dev/null
```

Olhar cada imagem (Read) e, nos vídeos, tirar 3 quadros com ffmpeg pro scratchpad e olhar. Se o vídeo tiver fala, transcrever (Transcritor em localhost:5001 ou a chave da AssemblyAI) pra usar na copy.

Regras de agrupamento:
- **Mesma arte em feed (1:1 ou 4:5) e vertical (9:16)** → um anúncio só, com cada arquivo no seu posicionamento. Vale pra imagem e pra vídeo.
- Arte sem par → anúncio de mídia única.
- Cards de carrossel (subpasta ou arquivos numerados da mesma sequência) → um anúncio de carrossel.
- Se não der pra ter certeza de que duas peças são a mesma arte, perguntar em vez de adivinhar.

## Passo 4. Nomes (padrão da SCI)

Anúncio: `AD<NN>_SCI_<TEMA>_<FORMATO>`, numerado a partir de 01, sem número depois do formato. Formato:
- `POST` imagem (com ou sem par vertical)
- `REELS` vídeo (com ou sem par)
- `CARROSSEL` carrossel

Arquivos, renomeados na própria pasta:
- mídia única: `AD01_SCI_<TEMA>_POST.png`
- par: `AD01_SCI_<TEMA>_POST_FEED.png` e `AD01_SCI_<TEMA>_POST_VERTICAL.png`
- carrossel: `AD03_SCI_<TEMA>_CARROSSEL_01.png`, `_02`, ...

Ordem dos números: imagens, depois vídeos, depois carrossel. Renomear só depois da aprovação do Passo 7, com `mv -n` (nunca sobrescrever).

## Passo 5. Textos

Rodar a skill `copy-meta-ads` com o site da live, os criativos (o que está escrito na arte e a fala do vídeo) e, como referência de estilo, os 5 textos e 5 títulos da live anterior (no `.json` do molde, em `asset_feed_spec.bodies` e `titles`).

- Anúncio de mídia única: **5 textos e 5 títulos** (a Meta combina).
- Anúncio com par feed + vertical ou carrossel: a API aceita **só 1 texto e 1 título**. Usar o mais forte dos 5 e dizer qual foi no plano.
- Todo texto termina chamando pro botão ("Clique em Saiba Mais e garanta sua vaga"), com data, hora e "online e gratuito".
- Título com até 40 caracteres de preferência.
- É material que vai pro público do cliente: tom profissional, sem gíria, zero travessão.

## Passo 6. Montar o plano

Salvar em `clientes/sci-sistemas/lives/<AAAA-MM-DD>-<tema-minusculo>/plano.json`:

```json
{
  "campanha_nome": "LIVE_CONTADOR_REFORMA_LEADS_SITE_11_11_26",
  "utm_id": "live_rt_111126",
  "link": "https://conteudo.sci.com.br/...",
  "orcamento_diario": 50.00,
  "inicio": "2026-10-29T09:00:00-0300",
  "fim": "2026-11-11T15:00:00-0300",
  "anuncios": [
    {"nome": "AD01_SCI_CONTADOR_REFORMA_POST", "tipo": "imagem",
     "arquivo": "/caminho/AD01_SCI_CONTADOR_REFORMA_POST.png", "arquivo_vertical": null,
     "textos": ["...", "...", "...", "...", "..."], "titulos": ["...", "...", "...", "...", "..."]},
    {"nome": "AD02_SCI_CONTADOR_REFORMA_REELS", "tipo": "video",
     "arquivo": "/caminho/AD02_..._REELS_FEED.mp4", "arquivo_vertical": "/caminho/AD02_..._REELS_VERTICAL.mp4",
     "textos": ["..."], "titulos": ["..."]},
    {"nome": "AD03_SCI_CONTADOR_REFORMA_CARROSSEL", "tipo": "carrossel",
     "cards": ["/caminho/..._01.png", "/caminho/..._02.png"],
     "textos": ["..."], "titulos": ["..."]}
  ]
}
```

Os caminhos do plano são os **nomes novos**, então o `plano.json` só é gravado depois do renome (Passo 8). `arquivo` é sempre o de feed quando há par.

## Passo 7. Conferir e pedir aprovação

Conferir os públicos (só lê):

```bash
python3 .claude/skills/campanha-live-sci/scripts/subir_live.py publicos
```

Público com menos de 1.000 pessoas ou com status diferente de Normal: avisar no plano.

Mostrar ao Arthur, num bloco só:

```
Live:       <título> · <data> às <hora>
Campanha:   LIVE_<TEMA>_LEADS_SITE_DD_MM_YY · CBO R$ X/dia · <início> até <fim>
Link:       <site>
UTM id:     <utm_id>

Conjuntos:  00_AUTO_LISTA_EMAIL · 02_AUTO_ENVOLVIMENTO_30D · 03_AUTO_ENVOLVIMENTO_365D · 03_AUTO_LOOKALIKE_2_ENVOLVIMENTO_30D

Renomear:
  arte-final-1.png           → AD01_SCI_<TEMA>_POST.png
  ...

Anúncios (em todos os conjuntos, PAUSED):
  AD01_SCI_<TEMA>_POST       imagem 4:5 · 5 textos, 5 títulos
  AD02_SCI_<TEMA>_REELS      vídeo 4:5 + 9:16 · 1 texto (o nº 3), 1 título

Textos e títulos: (listar todos)
```

Terminar com "Aprovo e subo?". Não renomear nem subir nada sem um sim claro.

## Passo 8. Renomear e subir

1. Renomear os arquivos (`mv -n`) e salvar o `plano.json` com os nomes novos.
2. Checar o plano (só lê: confere arquivos, medidas, quantidade de textos e públicos):

```bash
python3 .claude/skills/campanha-live-sci/scripts/subir_live.py checar --plano clientes/sci-sistemas/lives/<pasta>/plano.json
```

3. Subir:

```bash
python3 .claude/skills/campanha-live-sci/scripts/subir_live.py subir \
  --plano clientes/sci-sistemas/lives/<pasta>/plano.json \
  --estado clientes/sci-sistemas/lives/<pasta>/estado.json
```

Rodar **uma vez**. O `estado.json` guarda cada ID criado na hora; se der erro no meio, corrigir a causa e rodar o mesmo comando de novo, que ele continua de onde parou sem duplicar. Nunca apagar o `estado.json` com coisa já criada.

O script tira sozinho um recurso do Advantage+ criativo que a Meta recuse pelo nome pra aquele formato. Vídeo leva alguns minutos pra processar antes do criativo.

## Passo 9. Conferir e reportar

Ler de volta a campanha criada:

```bash
python3 .claude/skills/molde-meta/scripts/ler_molde.py --ids <ID_DA_CAMPANHA> --cliente sci-sistemas \
  --pasta clientes/sci-sistemas/lives/<pasta>/conferencia
```

Comparar com a tabela "O que já é fixo" e conferir:
- `targeting_automation.advantage_audience = 0` e `targeting_relaxation_types` com 0 nos 4 conjuntos
- `publisher_platforms` sem `audience_network`
- anúncio com par: `asset_feed_spec.optimization_type = PLACEMENT`, 2 mídias e 3 regras
- anúncio de mídia única: 5 textos e 5 títulos
- o mesmo `effective_object_story_id` pro mesmo anúncio nos 4 conjuntos
- UTMs com o `utm_id` certo

Reportar em tabela: campanha, conjuntos e anúncios com IDs, e qualquer diferença. Pedir pro Arthur olhar a prévia no Gerenciador (stories e reels principalmente) antes de ativar. Ativar só se ele pedir.

## Regras

- Tudo PAUSED. Nunca ativar sem pedido.
- Nunca mexer em campanha antiga da SCI.
- Não trocar públicos nem conjuntos sem o Arthur pedir. Mudou a regra, atualizar `config-sci.json` e este arquivo.
- Respostas pro Arthur em português, sem travessão.
