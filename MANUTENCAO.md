# Modo manutenção

Permite tirar o site do ar temporariamente e colocar uma página de aviso no
lugar, **renomeando um único arquivo pelo próprio GitHub** — sem mexer em
código e sem precisar do computador.

## Como funciona

O Netlify só lê o arquivo de redirecionamentos se ele se chamar exatamente
`_redirects`. Com qualquer outro nome, ele é ignorado. É só isso que liga e
desliga a manutenção:

| Nome do arquivo | Estado |
|---|---|
| `_redirects.off` | site normal (é como ele fica no dia a dia) |
| `_redirects` | manutenção ligada |

Quando ligado, a regra `/* /manutencao.html 200!` faz o Netlify entregar a
página de aviso em **qualquer** endereço do site, sem mudar a URL que aparece
no navegador.

## Ligar a manutenção

1. Abra o arquivo no GitHub:
   <https://github.com/abner-valente/landingPageRoyal/blob/main/_redirects.off>
2. Clique no ícone de lápis (**Edit this file**)
3. No campo do **nome do arquivo**, no topo, apague o sufixo `.off` — o nome
   deve ficar exatamente `_redirects`
4. Role até o fim e clique em **Commit changes**

Em menos de um minuto o site inteiro passa a mostrar a página de manutenção.

## Desligar

O mesmo caminho, ao contrário: abra o `_redirects`, edite o nome de volta para
`_redirects.off` e faça o commit. O site volta ao normal.

## Antes de ligar, vale conferir

A página de manutenção fica sempre acessível, mesmo com o modo desligado:

<https://royalimoveis.netlify.app/manutencao.html>

Dá para abrir esse endereço a qualquer momento para ver como ela está, sem
afetar o site.

## Detalhes que valem saber

**A página é autossuficiente.** O logo e o favicon estão embutidos nela, então
ela não depende de nenhum outro arquivo do site — que, durante a manutenção,
estaria sendo redirecionado também.

**O atendimento continua.** A página traz WhatsApp, telefone e Instagram em
destaque, além do link para as avaliações no Google. A ideia é que ninguém que
chegue ao site durante a manutenção vá embora sem ter como falar com a Royal.

**Não deixe ligado por muitos dias.** A página responde com status 200 e tem
`noindex`, que impede o Google de indexar "em manutenção" como se fosse o
conteúdo do site. O efeito colateral é que, se ficar ligado por muito tempo, o
Google pode tirar a home dos resultados. Para algumas horas ou um dia não há
problema; a reindexação volta sozinha depois. O ideal seria responder com
status 503, mas o Netlify só aceita 301, 302, 404 e 200 nas regras de
redirecionamento.

**O `_redirects.off` fica visível.** Como ele não é consumido pelo Netlify, o
arquivo acaba publicado em `/_redirects.off`. É inofensivo: contém apenas a
regra e comentários.
