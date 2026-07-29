# Sincronização com o Google

A nota e o número de avaliações exibidos na página são atualizados
automaticamente uma vez por dia, a partir do perfil da Royal no Google.

## Como funciona

1. Todo dia às 06:00 (horário de Brasília) o GitHub Actions roda
   `scripts/sync_google.py`. Em horários de pico o GitHub pode atrasar
   execuções agendadas em alguns minutos — isso é normal e não atrapalha.
2. O script consulta a **Places API (New)** do Google e lê dois campos:
   `rating` e `userRatingCount`.
3. Se algo mudou, ele reescreve os valores no `index.html`, atualiza o
   `dados-google.json` e faz commit.
4. O commit dispara o deploy automático do Netlify.

Se nada mudou, nenhum commit é criado. Se a consulta falhar, **nada é
alterado** — a página continua com o último valor bom, e a execução aparece
como falha no painel do GitHub.

## Atualizar na mão (funciona hoje, sem configurar nada)

Enquanto a chave da API não existir — ou sempre que quiser corrigir na hora —
dá para atualizar pelo painel do GitHub, sem mexer em código:

1. Aba **Actions → Sincroniza avaliações do Google → Run workflow**
2. Preencha **Total de avaliações** com o número que está no Google
3. **Nota** só se ela tiver mudado; vazio mantém a atual
4. **Run workflow**

O script reescreve os cinco pontos da página e as quatro tags de
compartilhamento, faz commit, e o Netlify publica. Leva menos de um minuto.

É o mesmo código do modo automático — muda só de onde vem o número, então não
existe risco de os dois caminhos divergirem.

## O que precisa ser configurado (uma vez só)

> **Sobre o pré-pagamento de R$200:** ele é exigido quando a forma de
> pagamento escolhida é **PIX**. Com **cartão de crédito**, o Google faz
> apenas uma verificação, sem depósito. Se a tela pedir os R$200, volte e
> troque a forma de pagamento. O valor pago vira crédito de uso e é
> reembolsável se a conta for encerrada sem consumo.

### 1. Chave da Places API

1. Acesse <https://console.cloud.google.com/> e crie um projeto.
2. Ative a **Places API (New)**.
3. Ative o faturamento no projeto (o Google exige, mesmo dentro da cota grátis).
4. Em *APIs e serviços → Credenciais*, crie uma **chave de API**.
5. Restrinja a chave à Places API. Não use restrição por HTTP referrer:
   quem chama é o GitHub Actions, não um navegador.

**Custo:** o SKU usado (*Place Details Enterprise*) inclui 1.000 chamadas
grátis por mês. Uma por dia dá cerca de 31, então fica em zero. Só cuidado
para não reaproveitar essa mesma chave em algo de alto volume.

### 2. Place ID do perfil

O código `cid=7411684396186397926` que aparece nos links da página **não** é
o Place ID. Pegue o correto na ferramenta oficial:
<https://developers.google.com/maps/documentation/places/web-service/place-id>

Busque por "Royal Imóveis RJ" e copie o identificador, que começa com `ChIJ`.

### 3. Segredos no GitHub

No repositório, em *Settings → Secrets and variables → Actions*, crie:

| Nome | Valor |
|---|---|
| `GOOGLE_MAPS_API_KEY` | a chave criada no passo 1 |
| `GOOGLE_PLACE_ID` | o Place ID do passo 2 |

> **Atenção: tem que ser na aba _Secrets_, não na aba _Variables_.** As duas
> ficam na mesma tela e é fácil confundir. A diferença importa por dois
> motivos: o workflow lê de `secrets`, então em *Variables* o valor
> simplesmente não chega; e *Variables* não são criptografadas nem mascaradas
> nos logs. Como este repositório é público e os logs de Actions de
> repositório público são visíveis para qualquer pessoa, uma chave guardada
> como variável pode vazar. Em *Secrets* ela aparece como `***`.

Guarde-os aí e em nenhum outro lugar. Eles nunca aparecem no código nem na
página publicada.

### 4. Testar

Em *Actions → Sincroniza avaliações do Google → Run workflow*, dispare na
mão. O log mostra o valor lido e se houve alteração.

## Onde mexer depois

- **Texto das tags de compartilhamento** (`description`, `og:title`,
  `og:image:alt`, `twitter:title`): edite em `scripts/sync_google.py`, na
  função `aplicar()`. Editar direto no `index.html` não adianta — a próxima
  sincronização sobrescreve.
- **Valores no corpo da página**: são os elementos marcados com
  `data-royal="count"` e `data-royal="rating"`. Pode mover de lugar ou criar
  novos, mas atualize a contagem esperada dentro de `aplicar()`, que falha de
  propósito se o número de marcadores não bater.
- **Horário**: campo `cron` em `.github/workflows/sync-google.yml`, em UTC.

## Detalhes que valem saber

- **A imagem de compartilhamento (`og-image.jpg`) não tem o número de
  avaliações desenhado**, de propósito. Ela não é regerada a cada
  sincronização, então um número ali envelheceria e contradiria a página.
- **Queda brusca interrompe a sincronização.** Se o total cair mais de 20%
  de um dia para o outro, o script para sem alterar nada. O Google remove
  avaliações falsas de vez em quando e uma queda pequena é normal; despencar
  merece um olhar humano.
- **O GitHub suspende agendamentos em repositórios parados.** Se o
  repositório ficar 60 dias sem nenhuma atividade, o agendamento é desativado
  e precisa ser reativado no painel de Actions.
