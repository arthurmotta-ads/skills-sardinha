# Skills Sardinha & Co. 🐟

Duas skills do Claude Code usadas na Sardinha & Co. para campanhas de captação no Meta Ads.

## copy-meta-ads

Gera 5 textos principais e 5 títulos para anúncios de leads no Meta Ads (inscrição em live, webinar, evento ou cadastro), cada texto com um ângulo diferente e no estilo de post orgânico.

Instalação: copiar a pasta `copy-meta-ads/` para `.claude/skills/` do seu projeto (ou `~/.claude/skills/` para usar em qualquer projeto). Não precisa de nenhuma configuração.

## campanha-live-sci

Sobe no Meta Ads, pela API, uma campanha de inscrição de live: 1 campanha CBO de Leads com 4 conjuntos (lista de e-mail, engajamento 30D, engajamento 365D e semelhante 2%), anúncios com feed e story da mesma arte juntos, UTMs padronizadas e tudo criado PAUSED. Foi feita para a SCI Sistemas, mas serve de modelo para qualquer conta que rode lives com o mesmo desenho.

### O que ela precisa

- A skill **meta-ads-ratos** instalada em `~/.claude/skills/meta-ads-ratos/`, com o token do Meta configurado. O script usa a biblioteca e o token dela.
- A skill **molde-meta** para a conferência no final (passo 9).
- A skill **copy-meta-ads** (deste repositório) para os textos.
- Python 3 com `facebook_business`.

### Configuração

1. Copiar `campanha-live-sci/` para `.claude/skills/`.
2. Copiar `config-sci.exemplo.json` para `config-sci.json` e preencher a conta de anúncio, a página, o Instagram, o pixel e os IDs dos 8 públicos personalizados.
3. Conferir os públicos: `python3 .claude/skills/campanha-live-sci/scripts/subir_live.py publicos`

O `config-sci.json` preenchido fica fora do Git (está no `.gitignore`).

### Uso

No Claude Code, rodar `/campanha-live-sci` com a pasta dos criativos, o link da página de inscrição, o orçamento diário e o período. A skill lê a página, junta as artes, escreve os textos, mostra o plano para aprovação e só então sobe.
