#!/usr/bin/env python3
"""
Campanha de live da SCI Sistemas no Meta Ads.

Três comandos:
  publicos                                         (só lê: confere se os 8 públicos existem e o tamanho)
  checar  --plano plano.json                       (só lê: arquivos, medidas e públicos)
  subir   --plano plano.json --estado estado.json  (cria tudo PAUSED, retoma de onde parou)

A configuração fixa da SCI (conta, página, pixel, públicos, conjuntos) fica em
../config-sci.json. O plano de cada live é montado pelo Claude seguindo o SKILL.md.

Usa o token e a lib da skill meta-ads-ratos.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
META_SCRIPTS = os.path.expanduser("~/.claude/skills/meta-ads-ratos/scripts")
sys.path.insert(0, META_SCRIPTS)

from lib import init_api  # noqa: E402

CONFIG = json.load(open(os.path.join(AQUI, "..", "config-sci.json"), encoding="utf-8"))

# Posições de feed (recebem o arquivo FEED quando o anúncio tem par feed + vertical).
# O resto (stories, reels, messenger) cai na regra geral e recebe o arquivo vertical.
FEED_FB = ["feed", "marketplace", "video_feeds", "search"]
FEED_IG = ["stream", "explore", "explore_home", "profile_feed", "ig_search"]

EXT_IMAGEM = {".png", ".jpg", ".jpeg"}
EXT_VIDEO = {".mp4", ".mov", ".m4v"}


def log(msg):
    print(msg, file=sys.stderr, flush=True)


# ---------------------------------------------------------------------------
# Plano e validações
# ---------------------------------------------------------------------------

def carregar_plano(caminho):
    plano = json.load(open(caminho, encoding="utf-8"))
    erros = []
    for campo in ("campanha_nome", "utm_id", "link", "orcamento_diario", "inicio", "fim", "anuncios"):
        if campo not in plano:
            erros.append(f"plano sem o campo '{campo}'")
    for ad in plano.get("anuncios", []):
        nome = ad.get("nome", "?")
        tipo = ad.get("tipo")
        if tipo not in ("imagem", "video", "carrossel"):
            erros.append(f"{nome}: tipo deve ser imagem, video ou carrossel")
        arquivos = ad.get("cards", []) if tipo == "carrossel" else [ad.get("arquivo"), ad.get("arquivo_vertical")]
        for a in filter(None, arquivos):
            if not os.path.isfile(a):
                erros.append(f"{nome}: arquivo não existe: {a}")
        tem_par = bool(ad.get("arquivo_vertical"))
        n_txt, n_tit = len(ad.get("textos", [])), len(ad.get("titulos", []))
        if n_txt < 1 or n_tit < 1:
            erros.append(f"{nome}: precisa de pelo menos 1 texto e 1 título")
        if (tem_par or tipo == "carrossel") and (n_txt > 1 or n_tit > 1):
            erros.append(f"{nome}: anúncio com par feed + vertical ou carrossel aceita só 1 texto e 1 título")
        if tipo == "carrossel" and not (2 <= len(ad.get("cards", [])) <= 10):
            erros.append(f"{nome}: carrossel precisa de 2 a 10 cards")
        if n_txt > 5 or n_tit > 5:
            erros.append(f"{nome}: máximo de 5 textos e 5 títulos")
    if erros:
        for e in erros:
            log("ERRO: " + e)
        sys.exit(1)
    return plano


def medidas(caminho):
    ext = os.path.splitext(caminho)[1].lower()
    if ext in EXT_IMAGEM:
        out = subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", caminho],
                             capture_output=True, text=True).stdout
        w = int(re.search(r"pixelWidth: (\d+)", out).group(1))
        h = int(re.search(r"pixelHeight: (\d+)", out).group(1))
        return w, h, None
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                          "-show_entries", "stream=width,height:format=duration",
                          "-of", "json", caminho], capture_output=True, text=True).stdout
    j = json.loads(out)
    s = j["streams"][0]
    return int(s["width"]), int(s["height"]), float(j["format"]["duration"])


def proporcao(w, h):
    r = w / h
    for nome, alvo in (("1:1", 1.0), ("4:5", 0.8), ("9:16", 0.5625), ("16:9", 1.778)):
        if abs(r - alvo) < 0.03:
            return nome
    return f"{w}x{h}"


def checar_publicos():
    from facebook_business.adobjects.customaudience import CustomAudience
    init_api()
    print("Públicos:")
    for chave, pid in CONFIG["publicos"].items():
        try:
            a = CustomAudience(pid).api_get(fields=["name", "approximate_count_lower_bound",
                                                    "approximate_count_upper_bound", "operation_status"])
            st = (a.get("operation_status") or {}).get("description", "")
            print(f"  ok  {a['name']} · {a.get('approximate_count_lower_bound')} a "
                  f"{a.get('approximate_count_upper_bound')} pessoas · {st}")
        except Exception as e:  # noqa: BLE001
            print(f"  ERRO {chave} ({pid}): {e}")


def cmd_publicos(args):
    checar_publicos()


def cmd_checar(args):
    plano = carregar_plano(args.plano)

    print(f"Campanha: {plano['campanha_nome']}")
    print(f"Orçamento diário: R$ {plano['orcamento_diario']:.2f} · {plano['inicio']} até {plano['fim']}")
    print(f"Link: {plano['link']}")
    print(f"UTMs: {CONFIG['url_tags'].replace('{UTM_ID}', plano['utm_id'])}")
    print()
    print("Anúncios:")
    for ad in plano["anuncios"]:
        arqs = ad["cards"] if ad["tipo"] == "carrossel" else [x for x in (ad.get("arquivo"), ad.get("arquivo_vertical")) if x]
        desc = []
        for a in arqs:
            w, h, dur = medidas(a)
            d = f"{os.path.basename(a)} ({proporcao(w, h)}"
            d += f", {dur:.0f}s)" if dur else ")"
            desc.append(d)
        print(f"  {ad['nome']} · {ad['tipo']} · {len(ad['textos'])} texto(s), {len(ad['titulos'])} título(s)")
        for d in desc:
            print(f"      {d}")
    print()
    checar_publicos()


# ---------------------------------------------------------------------------
# Criação
# ---------------------------------------------------------------------------

class Estado:
    def __init__(self, caminho):
        self.caminho = caminho
        self.d = json.load(open(caminho)) if os.path.exists(caminho) else {
            "midias": {}, "campanha": None, "conjuntos": {}, "criativos": {}, "anuncios": {}}

    def salvar(self):
        json.dump(self.d, open(self.caminho, "w"), indent=2, ensure_ascii=False)


def subir_imagem(conta, caminho, est):
    if caminho in est.d["midias"]:
        return est.d["midias"][caminho]
    from facebook_business.adobjects.adimage import AdImage
    img = AdImage(parent_id=conta)
    img[AdImage.Field.filename] = caminho
    img.remote_create()
    h = img[AdImage.Field.hash]
    est.d["midias"][caminho] = {"hash": h}
    est.salvar()
    log(f"  imagem {os.path.basename(caminho)} → {h}")
    return est.d["midias"][caminho]


def subir_video(conta, caminho, est):
    if caminho in est.d["midias"]:
        return est.d["midias"][caminho]
    from facebook_business.adobjects.advideo import AdVideo
    v = AdVideo(parent_id=conta)
    v[AdVideo.Field.filepath] = caminho
    v[AdVideo.Field.name] = os.path.basename(caminho)
    v.remote_create()
    vid = v["id"]
    log(f"  vídeo {os.path.basename(caminho)} → {vid}, esperando processar...")
    for _ in range(60):
        st = AdVideo(vid).api_get(fields=["status"]).get("status", {}).get("video_status")
        if st == "ready":
            break
        if st == "error":
            raise RuntimeError(f"Meta não conseguiu processar o vídeo {caminho}")
        time.sleep(10)
    else:
        raise RuntimeError(f"vídeo {caminho} não ficou pronto em 10 minutos, rodar de novo depois")
    thumbs = list(AdVideo(vid).get_thumbnails(fields=["uri", "is_preferred"]))
    pref = next((t for t in thumbs if t.get("is_preferred")), thumbs[0] if thumbs else None)
    est.d["midias"][caminho] = {"video_id": vid, "thumb": pref["uri"] if pref else None}
    est.salvar()
    return est.d["midias"][caminho]


def subir_midia(conta, caminho, est):
    ext = os.path.splitext(caminho)[1].lower()
    return subir_video(conta, caminho, est) if ext in EXT_VIDEO else subir_imagem(conta, caminho, est)


def recursos_desligados(lista):
    return {"creative_features_spec": {k: {"enroll_status": "OPT_OUT"} for k in lista}}


def criar_criativo(conta, nome, params):
    """Cria o criativo com todos os recursos do Advantage+ criativo desligados.
    Se a Meta recusar algum recurso pelo nome (não vale pro formato), tira ele e tenta de novo."""
    from facebook_business.adobjects.adaccount import AdAccount
    from facebook_business.exceptions import FacebookRequestError
    lista = list(CONFIG["recursos_desligados"])
    for _ in range(15):
        p = dict(params)
        p["name"] = nome
        p["degrees_of_freedom_spec"] = recursos_desligados(lista)
        try:
            return AdAccount(conta).create_ad_creative(params=p)["id"]
        except FacebookRequestError as e:
            texto = " ".join(str(x) for x in (e.api_error_message(), e.body()))
            ruins = [k for k in lista if re.search(rf"\b{re.escape(k)}\b", texto)]
            if not ruins:
                raise
            log(f"  Meta recusou {ruins} em {nome}, tirando e tentando de novo")
            lista = [k for k in lista if k not in ruins]
    raise RuntimeError(f"não consegui criar o criativo {nome}")


def montar_criativo(conta, plano, ad, est):
    base_oss = {"page_id": CONFIG["pagina_id"], "instagram_user_id": CONFIG["instagram_id"]}
    link = plano["link"]
    botao = CONFIG["botao"]
    url_tags = CONFIG["url_tags"].replace("{UTM_ID}", plano["utm_id"])
    textos = [{"text": t} for t in ad["textos"]]
    titulos = [{"text": t} for t in ad["titulos"]]

    if ad["tipo"] == "carrossel":
        cards = []
        for c in ad["cards"]:
            m = subir_imagem(conta, c, est)
            cards.append({"link": link, "image_hash": m["hash"], "name": ad["titulos"][0]})
        oss = dict(base_oss)
        oss["link_data"] = {
            "link": link,
            "message": ad["textos"][0],
            "child_attachments": cards,
            "call_to_action": {"type": botao, "value": {"link": link}},
            "multi_share_end_card": True,
            "multi_share_optimized": False,
        }
        return {"object_story_spec": oss, "url_tags": url_tags, "instagram_user_id": CONFIG["instagram_id"]}

    principal = subir_midia(conta, ad["arquivo"], est)
    e_video = "video_id" in principal

    if not ad.get("arquivo_vertical"):
        # Mídia única com até 5 textos e 5 títulos (a Meta combina)
        afs = {
            "bodies": textos,
            "titles": titulos,
            "link_urls": [{"website_url": link}],
            "call_to_action_types": [botao],
            "optimization_type": "DEGREES_OF_FREEDOM",
        }
        if e_video:
            afs["videos"] = [{"video_id": principal["video_id"], "thumbnail_url": principal["thumb"]}]
            afs["ad_formats"] = ["SINGLE_VIDEO"]
        else:
            afs["images"] = [{"hash": principal["hash"]}]
            afs["ad_formats"] = ["SINGLE_IMAGE"]
        return {"object_story_spec": base_oss, "asset_feed_spec": afs, "url_tags": url_tags,
                "instagram_user_id": CONFIG["instagram_id"]}

    # Par feed + vertical: mídia por posicionamento, 1 texto e 1 título
    vertical = subir_midia(conta, ad["arquivo_vertical"], est)
    lf, lv = f"feed-{ad['nome'].lower()}", f"vertical-{ad['nome'].lower()}"
    afs = {
        "bodies": textos,
        "titles": titulos,
        "link_urls": [{"website_url": link}],
        "call_to_action_types": [botao],
        "ad_formats": ["AUTOMATIC_FORMAT"],
    }
    chave_label = "video_label" if e_video else "image_label"
    if e_video:
        afs["videos"] = [
            {"video_id": principal["video_id"], "thumbnail_url": principal["thumb"], "adlabels": [{"name": lf}]},
            {"video_id": vertical["video_id"], "thumbnail_url": vertical["thumb"], "adlabels": [{"name": lv}]},
        ]
    else:
        afs["images"] = [
            {"hash": principal["hash"], "adlabels": [{"name": lf}]},
            {"hash": vertical["hash"], "adlabels": [{"name": lv}]},
        ]
    afs["asset_customization_rules"] = [
        {"customization_spec": {"publisher_platforms": ["facebook"], "facebook_positions": FEED_FB},
         chave_label: {"name": lf}, "priority": 1},
        {"customization_spec": {"publisher_platforms": ["instagram"], "instagram_positions": FEED_IG},
         chave_label: {"name": lf}, "priority": 2},
        {"customization_spec": {}, chave_label: {"name": lv}, "priority": 3},
    ]
    return {"object_story_spec": base_oss, "asset_feed_spec": afs, "url_tags": url_tags,
            "instagram_user_id": CONFIG["instagram_id"]}


def targeting_do_conjunto(cj):
    pub = CONFIG["publicos"]
    t = {
        "geo_locations": {"countries": ["BR"], "location_types": ["home", "recent"]},
        "age_min": CONFIG["idade_min"],
        "age_max": CONFIG["idade_max"],
        "custom_audiences": [{"id": pub[k]} for k in cj["incluir"]],
        "publisher_platforms": CONFIG["plataformas"],
        "targeting_automation": {"advantage_audience": 0},
        "targeting_relaxation_types": {"lookalike": 0, "custom_audience": 0},
    }
    if cj["excluir"]:
        t["excluded_custom_audiences"] = [{"id": pub[k]} for k in cj["excluir"]]
    return t


def cmd_subir(args):
    plano = carregar_plano(args.plano)
    init_api()
    from facebook_business.adobjects.adaccount import AdAccount
    conta = CONFIG["conta"]
    acc = AdAccount(conta)
    est = Estado(args.estado)

    # 1. Campanha (CBO, orçamento diário)
    if not est.d["campanha"]:
        c = acc.create_campaign(params={
            "name": plano["campanha_nome"],
            "objective": "OUTCOME_LEADS",
            "buying_type": "AUCTION",
            "special_ad_categories": [],
            "daily_budget": int(round(plano["orcamento_diario"] * 100)),
            "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
            "status": "PAUSED",
        })
        est.d["campanha"] = c["id"]
        est.salvar()
        log(f"campanha {plano['campanha_nome']} → {c['id']}")

    # 2. Conjuntos
    for cj in CONFIG["conjuntos"]:
        if cj["nome"] in est.d["conjuntos"]:
            continue
        s = acc.create_ad_set(params={
            "name": cj["nome"],
            "campaign_id": est.d["campanha"],
            "optimization_goal": "OFFSITE_CONVERSIONS",
            "billing_event": "IMPRESSIONS",
            "promoted_object": {"pixel_id": CONFIG["pixel_id"], "custom_event_type": CONFIG["evento"]},
            "attribution_spec": CONFIG["atribuicao"],
            "targeting": targeting_do_conjunto(cj),
            "start_time": plano["inicio"],
            "end_time": plano["fim"],
            "status": "PAUSED",
        })
        est.d["conjuntos"][cj["nome"]] = s["id"]
        est.salvar()
        log(f"conjunto {cj['nome']} → {s['id']}")

    # 3. Criativos (um por anúncio, reaproveitado nos 4 conjuntos = mesmo post)
    for ad in plano["anuncios"]:
        if ad["nome"] in est.d["criativos"]:
            continue
        params = montar_criativo(conta, plano, ad, est)
        cid = criar_criativo(conta, ad["nome"], params)
        est.d["criativos"][ad["nome"]] = cid
        est.salvar()
        log(f"criativo {ad['nome']} → {cid}")

    # 4. Anúncios
    for cj in CONFIG["conjuntos"]:
        for ad in plano["anuncios"]:
            chave = f"{cj['nome']}|{ad['nome']}"
            if chave in est.d["anuncios"]:
                continue
            a = acc.create_ad(params={
                "name": ad["nome"],
                "adset_id": est.d["conjuntos"][cj["nome"]],
                "creative": {"creative_id": est.d["criativos"][ad["nome"]]},
                "status": "PAUSED",
            })
            est.d["anuncios"][chave] = a["id"]
            est.salvar()
            log(f"anúncio {ad['nome']} em {cj['nome']} → {a['id']}")
            time.sleep(1)

    print(json.dumps(est.d, indent=2, ensure_ascii=False))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("publicos")
    a = sub.add_parser("checar")
    a.add_argument("--plano", required=True)
    b = sub.add_parser("subir")
    b.add_argument("--plano", required=True)
    b.add_argument("--estado", required=True, help="arquivo de IDs criados (retoma se já existir)")
    args = p.parse_args()
    {"publicos": cmd_publicos, "checar": cmd_checar, "subir": cmd_subir}[args.cmd](args)


if __name__ == "__main__":
    main()
