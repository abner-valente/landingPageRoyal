"""
Sincroniza a nota e o numero de avaliacoes do perfil da Royal no Google
com o index.html.

Roda uma vez por dia pelo GitHub Actions (.github/workflows/sync-google.yml).
Se a API falhar ou devolver algo implausivel, sai SEM tocar no arquivo:
um numero de ontem e melhor que um numero errado no ar.

Tem dois modos:

  AUTOMATICO  le do Google. Precisa de GOOGLE_MAPS_API_KEY e GOOGLE_PLACE_ID.
  MANUAL      voce informa os numeros em ROYAL_COUNT / ROYAL_RATING, e a API
              nem e chamada. Serve enquanto a chave nao existe e tambem como
              atalho para corrigir na mao a qualquer momento.

O caminho que reescreve o HTML e exatamente o mesmo nos dois casos; muda so
de onde vem o numero.

Variaveis de ambiente:
  GOOGLE_MAPS_API_KEY  chave da Places API (New)
  GOOGLE_PLACE_ID      Place ID do perfil da Royal no Google
  ROYAL_COUNT          (modo manual) total de avaliacoes, ex: 290
  ROYAL_RATING         (modo manual) nota, ex: 5,0 -- opcional, mantem a atual

Codigos de saida: 0 = ok (mudou ou nao), 1 = falhou sem alterar nada.
"""

import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.request

RAIZ = pathlib.Path(__file__).resolve().parent.parent
HTML = RAIZ / "index.html"
ESTADO = RAIZ / "dados-google.json"

ENDPOINT = "https://places.googleapis.com/v1/places/{}"

# Queda maior que isto e tratada como suspeita e interrompe a sincronizacao.
# O Google remove avaliacoes falsas de vez em quando, entao cair um pouco e
# normal; despencar nao e, e nesse caso vale um olhar humano.
QUEDA_MAXIMA = 0.20


def buscar(place_id: str, chave: str) -> dict:
    req = urllib.request.Request(
        ENDPOINT.format(place_id),
        headers={
            "X-Goog-Api-Key": chave,
            "X-Goog-FieldMask": "rating,userRatingCount",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def validar(dados: dict) -> tuple[float, int]:
    nota = dados.get("rating")
    total = dados.get("userRatingCount")
    if not isinstance(total, int) or total < 1:
        raise ValueError(f"userRatingCount implausivel: {total!r}")
    if not isinstance(nota, (int, float)) or not 0 < float(nota) <= 5:
        raise ValueError(f"rating implausivel: {nota!r}")
    return float(nota), total


def ler_estado() -> dict:
    if ESTADO.exists():
        return json.loads(ESTADO.read_text(encoding="utf-8"))
    return {}


def aplicar(html: str, nota_txt: str, total: int) -> str:
    """Reescreve os valores no HTML. Levanta se a estrutura esperada sumiu."""
    html, n = re.subn(r'(data-royal="count">)[^<]*(<)', lambda m: f"{m[1]}{total}{m[2]}", html)
    if n != 3:
        raise ValueError(f"esperava 3 marcadores data-royal=count, encontrei {n}")

    html, n = re.subn(r'(data-royal="rating">)[^<]*(<)', lambda m: f"{m[1]}{nota_txt}{m[2]}", html)
    if n != 2:
        raise ValueError(f"esperava 2 marcadores data-royal=rating, encontrei {n}")

    # As tags abaixo sao reescritas por inteiro. Para mudar o texto delas,
    # edite AQUI -- editar no index.html nao adianta, a proxima sync desfaz.
    titulo = f"Royal Imóveis RJ — nota {nota_txt} em {total} avaliações no Google"
    descricao = (
        f"Royal Imóveis RJ tem nota {nota_txt} no Google, com {total} avaliações de "
        "clientes reais. Leia os depoimentos de quem comprou, vendeu e alugou com a "
        "corretora na Freguesia, Jacarepaguá, Rio de Janeiro."
    )
    alt = f"Royal Imóveis RJ — nota {nota_txt} com {total} avaliações no Google"

    tags = [
        (r'<meta name="description" content="[^"]*">',
         f'<meta name="description" content="{descricao}">'),
        (r'<meta property="og:title" content="[^"]*">',
         f'<meta property="og:title" content="{titulo}">'),
        (r'<meta property="og:image:alt" content="[^"]*">',
         f'<meta property="og:image:alt" content="{alt}">'),
        (r'<meta name="twitter:title" content="[^"]*">',
         f'<meta name="twitter:title" content="{titulo}">'),
    ]
    for padrao, novo in tags:
        html, n = re.subn(padrao, lambda m, v=novo: v, html)
        if n != 1:
            raise ValueError(f"esperava 1 ocorrencia de {padrao!r}, encontrei {n}")

    return html


def main() -> int:
    anterior = ler_estado()
    manual = os.environ.get("ROYAL_COUNT", "").strip()

    if manual:
        # ---- modo manual: nao chama a API
        nota_manual = os.environ.get("ROYAL_RATING", "").strip().replace(",", ".")
        try:
            nota, total = validar({
                "rating": float(nota_manual) if nota_manual else anterior.get("rating", 5.0),
                "userRatingCount": int(manual),
            })
        except (ValueError, TypeError) as e:
            print(f"ERRO nos valores informados a mao: {e}", file=sys.stderr)
            return 1
        print(f"Modo manual: nota {nota}, {total} avaliacoes.")
    else:
        # ---- modo automatico: le do Google
        chave = os.environ.get("GOOGLE_MAPS_API_KEY", "").strip()
        place_id = os.environ.get("GOOGLE_PLACE_ID", "").strip()
        if not chave or not place_id:
            # Sem credenciais ainda. Avisa sem quebrar a execucao agendada,
            # para nao gerar e-mail de falha todo dia enquanto nao houver chave.
            print("::warning::Sincronizacao automatica desligada: faltam "
                  "GOOGLE_MAPS_API_KEY e GOOGLE_PLACE_ID. Veja SINCRONIZACAO.md.")
            return 0
        try:
            nota, total = validar(buscar(place_id, chave))
        except urllib.error.HTTPError as e:
            print(f"ERRO: Google respondeu HTTP {e.code}: "
                  f"{e.read().decode('utf-8', 'replace')[:400]}", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"ERRO ao consultar o Google: {e}", file=sys.stderr)
            return 1

    total_antes = anterior.get("userRatingCount")
    if isinstance(total_antes, int) and total < total_antes * (1 - QUEDA_MAXIMA):
        print(
            f"ERRO: numero de avaliacoes caiu de {total_antes} para {total} "
            f"(mais de {QUEDA_MAXIMA:.0%}). Nada foi alterado; confira o perfil no Google.",
            file=sys.stderr,
        )
        return 1

    nota_txt = f"{nota:.1f}".replace(".", ",")
    original = HTML.read_text(encoding="utf-8")
    try:
        novo = aplicar(original, nota_txt, total)
    except ValueError as e:
        print(f"ERRO: o index.html nao esta na estrutura esperada -- {e}", file=sys.stderr)
        return 1

    if novo == original and total_antes == total:
        print(f"Sem mudanca: nota {nota_txt}, {total} avaliacoes.")
        return 0

    HTML.write_text(novo, encoding="utf-8")
    ESTADO.write_text(
        json.dumps({"rating": nota, "userRatingCount": total}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Atualizado: nota {nota_txt}, {total} avaliacoes (antes: {total_antes}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
