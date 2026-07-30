# Sincronização com o Google

A nota e o número de avaliações exibidos na página são atualizados por um
script, para que nunca fiquem defasados em relação ao perfil da Royal no
Google.

**Hoje o projeto opera em modo manual.** A leitura automática exige uma conta
de faturamento no Google Cloud, cuja criação pede um pré-pagamento, e essa
decisão ficou em espera. Todo o código do modo automático está pronto e
testado; falta só a credencial funcionar. O agendamento diário está
desativado de propósito, para não gerar erro todo dia.

## Como atualizar (o procedimento do dia a dia)

Confira o número no perfil do Google. Se mudou:

1. Abra **Actions → Sincroniza avaliações do Google → Run workflow**
2. Em **Total de avaliações**, digite o número novo — o campo é obrigatório
3. **Nota**: deixe vazio, a não ser que ela tenha mudado de 5,0
4. **Run workflow**

Em menos de um minuto o número está no ar. O script reescreve os cinco pontos
da página e as quatro tags de compartilhamento, faz commit, e o Netlify
publica sozinho.

> **Não edite o `dados-google.json` na mão.** Ele não é a fonte do número: é
> um registro do último valor gravado, escrito pelo próprio script e usado
> para comparar de uma execução para outra. Mudar ele não altera a página, e
> um valor inventado ali pode fazer o script recusar a próxima atualização,
> por parecer uma queda brusca. O único lugar onde você informa o número é o
> campo do formulário.

Se você digitar o número que já está publicado, o script percebe e não faz
nada — nenhum commit, nenhum deploy. Repetir é seguro.

## O que muda quando o automático for ligado

Nada no procedimento acima: ele continua valendo como atalho de correção. O
automático apenas passa a rodar sozinho todo dia de manhã. É o mesmo código
nos dois modos — muda só de onde vem o número, então os dois caminhos não têm
como divergir.

Para religar, veja os comentários no topo de
`.github/workflows/sync-google.yml`.

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
