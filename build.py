#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genera il sito statico di Bilancia Civica in ``_site/``.

Uso:
    python3 build.py            # scrive _site/
    python3 -m http.server -d _site 8000   # anteprima su http://localhost:8000

Solo libreria standard di Python (3.9+). Nessuna dipendenza esterna, nessun
cookie, nessun tracciamento, nessuno script: il sito è HTML e CSS puri.

I testi stanno in ``contenuti/*.md`` (Markdown semplice con intestazione
``---``) e, per i documenti lunghi, in ``METODOLOGIA.md``, ``CONTRIBUTING.md``
e ``docs/*.md``. Il convertitore Markdown qui sotto supporta solo ciò che
serve a questi file: titoli, paragrafi, elenchi (anche annidati), tabelle,
citazioni, blocchi di codice, riquadri ``::: tipo`` e testo in linea
(grassetto, corsivo, codice, link). Le etichette [FATTO], [STIMA],
[INTERPRETAZIONE] e [DA VERIFICARE] diventano badge colorati.
"""
from __future__ import annotations

import html
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "_site"

# Indirizzo del repository pubblico (per «segnala un errore» e «codice sorgente»).
# Da aggiornare se il repository avrà un nome diverso.
REPO_URL = "https://github.com/BilanciaCivica/bilancia-civica"
# Data mostrata nel piè di pagina («Testi aggiornati al …»). Va aggiornata a mano
# ogni volta che si modificano i contenuti, insieme alle date nelle singole pagine.
AGGIORNATO = "24/10/2026, ore 10:42 (ora di Roma)"

# Pagine: (file di uscita, sorgente, voce di menu principale o None, gruppo)
PAGINE = [
    ("index.html", "contenuti/home.md", "Home", None),
    ("diritti.html", "contenuti/diritti.md", "Diritti e regole", "diritti"),
    ("presidio.html", "contenuti/presidio.md", None, "diritti"),
    ("corteo.html", "contenuti/corteo.md", None, "diritti"),
    ("sciopero.html", "contenuti/sciopero.md", None, "diritti"),
    ("decreto.html", "contenuti/decreto.md", "Decreto sicurezza", "diritti"),
    ("esempio.html", "contenuti/esempio.md", None, "diritti"),
    ("stato.html", "contenuti/stato.md", None, None),
    ("impatto.html", "contenuti/impatto.md", None, None),
    ("alternative.html", "contenuti/alternative.md", None, None),
    ("fonti.html", "contenuti/fonti.md", None, None),
    ("metodo.html", "METODOLOGIA.md", None, None),
    ("contribuisci.html", "CONTRIBUTING.md", None, None),
    ("bussola-completa.html", "docs/bussola-diritti.md", None, "documenti"),
    ("analisi-dl-190-2026.html", "docs/analisi-dl-190-2026.md", None, "documenti"),
    ("glossario.html", "contenuti/glossario.md", "Glossario", None),
    ("chi-siamo.html", "contenuti/chi-siamo.md", "Chi siamo", None),
    ("note-legali.html", "contenuti/note-legali.md", None, None),
    ("404.html", "contenuti/404.md", None, None),
]
SOTTOMENU_DIRITTI = [
    ("diritti.html", "Panoramica"),
    ("presidio.html", "Presidio"),
    ("corteo.html", "Corteo"),
    ("sciopero.html", "Sciopero"),
    ("decreto.html", "Decreto sicurezza"),
    ("esempio.html", "Scheda completa: corteo e decreto"),
    ("bussola-completa.html", "Testo completo"),
]
# Link Markdown tra file del repository -> pagine del sito
MAPPA_LINK = {src: out for out, src, _, _ in PAGINE}
MAPPA_LINK.update({"LICENSE": REPO_URL + "/blob/main/LICENSE",
                   "LICENSE-TESTI": REPO_URL + "/blob/main/LICENSE-TESTI", "README.md": "index.html"})

CSP = ("default-src 'none'; style-src 'self'; img-src 'self'; "
       "base-uri 'none'; form-action 'none'")


# ---------------------------------------------------------------------------
# Markdown minimo
# ---------------------------------------------------------------------------
def slug(testo: str) -> str:
    """Ancora compatibile con GitHub (lettere, cifre, trattini)."""
    t = re.sub(r"<[^>]+>", "", testo).strip().lower()
    t = re.sub(r"[^\w\- ]", "", t, flags=re.UNICODE)
    return t.replace(" ", "-")


ETICHETTE = {
    "FATTO": "fatto", "STIMA": "stima", "INTERPRETAZIONE": "interp",
    "DA VERIFICARE": "verif",
}
# Spiegazione in una riga di ogni etichetta (tooltip e legenda in fondo alle pagine)
SPIEGAZIONE = {
    "FATTO": "si può controllare sulla fonte indicata (legge, sentenza, atto ufficiale)",
    "STIMA": "un calcolo su numeri, sempre come intervallo da… a…, con ipotesi dichiarate",
    "INTERPRETAZIONE": "un'opinione o una lettura, sempre con il nome di chi la esprime",
    "DA VERIFICARE": "non ancora confermato da una fonte ufficiale: diciamo cosa manca",
}
RE_ETICHETTA = re.compile(
    r"\[(FATTO|STIMA|INTERPRETAZIONE|DA VERIFICARE)((?:[ ·,][^\[\]]*)?)\]"
    r"|\b(FATTO|DA VERIFICARE)(, certezza (?:Alta|Media|Bassa))"
)
RE_NOTA = re.compile(r"\[(Nota redazionale di Bilancia Civica[^\[\]]*)\]")


SCHEMI_AMMESSI = ("https://", "http://", "mailto:")


def link_sicuro(url: str) -> bool:
    """Ammette solo https, http, mailto, link relativi e ancore.

    Scarta javascript:, data:, vbscript:, file: e qualunque altro schema, anche
    se scritto con maiuscole, spazi o caratteri di controllo per mascherarlo.
    """
    pulito = re.sub(r"[\x00-\x20\x7f]", "", url).lower()
    if pulito.startswith(SCHEMI_AMMESSI):
        return True
    if pulito.startswith("//"):
        return False  # URL senza schema verso un altro dominio
    return re.match(r"^[a-z][a-z0-9+.-]*:", pulito) is None


def _link(url: str) -> str:
    if url.lower().startswith(SCHEMI_AMMESSI):
        return url  # URL assoluto: non va riscritto (anche se finisce in .md)
    base, _, ancora = url.partition("#")
    while base.startswith("../"):
        base = base[3:]
    if base in MAPPA_LINK:
        base = MAPPA_LINK[base]
    elif base.startswith("docs/") or base.endswith(".md"):
        base = REPO_URL + "/blob/main/" + base
    return base + ("#" + ancora if ancora else "")


def inline(testo: str) -> str:
    segnaposto: list[str] = []

    def keep(s: str) -> str:
        segnaposto.append(s)
        return f"\x00{len(segnaposto) - 1}\x00"

    t = re.sub(r"\[((?:[^\[\]]|\[[^\[\]]*\])+)\]\(([^)\s]+)\)",
               lambda m: keep("\x01" + m.group(1) + "\x02" + m.group(2) + "\x03"), testo)
    t = re.sub(r"`([^`]+)`", lambda m: keep("<code>" + html.escape(m.group(1)) + "</code>"), t)
    t = html.escape(t, quote=False)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", t)

    def badge(m: re.Match) -> str:
        nome = m.group(1) or m.group(3)
        resto = (m.group(2) or m.group(4) or "")
        return ('<span class="etichetta">'
                + f'<span class="et et-{ETICHETTE[nome]}" title="{nome}: {html.escape(SPIEGAZIONE[nome], quote=True)}">{nome}</span>'
                + (f'<span class="et-extra">{resto.strip(" ,")}</span>' if resto.strip(" ·,") else "")
                + "</span>")

    t = RE_ETICHETTA.sub(badge, t)
    t = RE_NOTA.sub(r'<span class="et et-nota">\1</span>', t)

    def restore(m: re.Match) -> str:
        s = segnaposto[int(m.group(1))]
        if s.startswith("\x01"):
            testo_link, url = s[1:-1].split("\x02")
            if not link_sicuro(url):
                print(f"ATTENZIONE: link scartato (schema non ammesso): {url!r}", file=sys.stderr)
                return inline(testo_link)
            href = html.escape(_link(url), quote=True)
            est = href.startswith("http")
            attr = ' rel="noopener noreferrer"' if est else ""
            return f'<a href="{href}"{attr}>{inline(testo_link)}</a>'
        return s

    while "\x00" in t:
        t = re.sub(r"\x00(\d+)\x00", restore, t)
    return t


def _celle(riga: str) -> list[str]:
    riga = riga.strip()
    if riga.startswith("|"):
        riga = riga[1:]
    if riga.endswith("|"):
        riga = riga[:-1]
    return [c.strip() for c in riga.split("|")]


RE_LI = re.compile(r"^(\s*)([-*•]|\d+\.)\s+(.*)$")


def _lista(righe: list[str], i: int) -> tuple[str, int]:
    m = RE_LI.match(righe[i])
    rientro = len(m.group(1))
    ordinata = m.group(2)[0].isdigit()
    tag = "ol" if ordinata else "ul"
    start = int(m.group(2)[:-1]) if ordinata else 1
    out = [f'<{tag}{" start=" + chr(34) + str(start) + chr(34) if ordinata and start != 1 else ""}>']
    voce: list[str] | None = None
    while i < len(righe):
        r = righe[i]
        m = RE_LI.match(r)
        if m and len(m.group(1)) == rientro:
            if voce is not None:
                out.append("<li>" + "".join(voce) + "</li>")
            voce = [inline(m.group(3))]
            i += 1
        elif m and len(m.group(1)) > rientro:
            sotto, i = _lista(righe, i)
            voce.append(sotto)
        elif r.strip().startswith("```") and r.startswith(" " * (rientro + 2)) and voce is not None:
            j = i + 1
            while j < len(righe) and not righe[j].strip().startswith("```"):
                j += 1
            codice = [x[rientro + 2:] if x.startswith(" " * (rientro + 2)) else x.strip() for x in righe[i + 1:j]]
            voce.append("<pre><code>" + html.escape("\n".join(codice)) + "</code></pre>")
            i = j + 1
        elif r.strip() and not m and r.startswith(" " * (rientro + 2)):
            voce.append(" " + inline(r.strip()))  # continuazione della voce
            i += 1
        else:
            break
    if voce is not None:
        out.append("<li>" + "".join(voce) + "</li>")
    out.append(f"</{tag}>")
    return "\n".join(out), i


def markdown(testo: str, toc: list | None = None) -> str:
    righe = testo.replace("\r\n", "\n").split("\n")
    out: list[str] = []
    i = 0
    while i < len(righe):
        r = righe[i]
        s = r.strip()
        if not s or s.startswith("<!--"):
            i += 1
            continue
        if s.startswith("```"):
            j = i + 1
            while j < len(righe) and not righe[j].strip().startswith("```"):
                j += 1
            out.append("<pre><code>" + html.escape("\n".join(righe[i + 1:j])) + "</code></pre>")
            i = j + 1
            continue
        if s.startswith(":::"):
            tipo = s[3:].strip() or "nota"
            # Riquadri annidabili: ogni "::: tipo" apre, ogni ":::" chiude
            j = i + 1
            profondita = 1
            while j < len(righe):
                sj = righe[j].strip()
                if sj == ":::":
                    profondita -= 1
                    if profondita == 0:
                        break
                elif sj.startswith(":::"):
                    profondita += 1
                j += 1
            interno = markdown("\n".join(righe[i + 1:j]))
            if tipo.startswith("dettagli"):
                # Sezione richiudibile in HTML puro (<details>), senza script
                titolo_det = inline(tipo[len("dettagli"):].strip() or "Dettagli e fonti")
                out.append(f'<details class="dettagli"><summary>{titolo_det}</summary>{interno}</details>')
                i = j + 1
                continue
            if tipo == "scelte":
                out.append(f'<nav class="scelte" aria-label="Scegli un argomento">{interno}</nav>')
                i = j + 1
                continue
            out.append(f'<div class="box box-{html.escape(tipo)}">' + interno + "</div>")
            i = j + 1
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", s)
        if m:
            liv = len(m.group(1))
            contenuto = inline(m.group(2))
            ident = slug(contenuto)
            if toc is not None and liv == 2:
                toc.append((ident, contenuto))
            out.append(f'<h{liv} id="{ident}">{contenuto}</h{liv}>')
            i += 1
            continue
        if re.match(r"^(-{3,}|\*{3,})$", s):
            out.append("<hr>")
            i += 1
            continue
        if s.startswith(">"):
            blocco = []
            while i < len(righe) and righe[i].strip().startswith(">"):
                blocco.append(re.sub(r"^\s*>\s?", "", righe[i]))
                i += 1
            out.append("<blockquote>" + markdown("\n".join(blocco)) + "</blockquote>")
            continue
        if s.startswith("|") and i + 1 < len(righe) and re.match(r"^\s*\|?\s*:?-{3,}", righe[i + 1]):
            testata = _celle(s)
            i += 2
            corpo = []
            while i < len(righe) and righe[i].strip().startswith("|"):
                corpo.append(_celle(righe[i]))
                i += 1
            t = ['<div class="tabella"><table>', "<thead><tr>"]
            t += [f"<th scope=\"col\">{inline(c)}</th>" for c in testata]
            t.append("</tr></thead><tbody>")
            for riga in corpo:
                t.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in riga) + "</tr>")
            t.append("</tbody></table></div>")
            out.append("".join(t))
            continue
        if RE_LI.match(r):
            blocco, i = _lista(righe, i)
            out.append(blocco)
            continue
        par = []
        while i < len(righe):
            q = righe[i].strip()
            if (not q or q.startswith(("#", ">", "```", ":::", "|", "<!--"))
                    or RE_LI.match(righe[i]) or re.match(r"^(-{3,}|\*{3,})$", q)):
                break
            par.append(inline(q))
            i += 1
        out.append("<p>" + "<br>\n".join(par) + "</p>")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Pagine
# ---------------------------------------------------------------------------
def leggi(sorgente: str) -> tuple[dict, str]:
    testo = (ROOT / sorgente).read_text(encoding="utf-8").replace("{{REPO}}", REPO_URL).replace("{{AGGIORNATO}}", AGGIORNATO)
    meta: dict = {}
    if testo.startswith("---\n"):
        fine = testo.index("\n---\n", 4)
        for riga in testo[4:fine].splitlines():
            k, _, v = riga.partition(":")
            meta[k.strip()] = v.strip()
        testo = testo[fine + 5:]
    else:
        m = re.search(r"^#\s+(.+)$", testo, re.M)
        meta["titolo"] = re.sub(r"[*`]", "", m.group(1)) if m else sorgente
    return meta, testo


def menu(attivo: str, gruppo: str | None) -> str:
    voci = []
    principali = {o for o, _, v, _ in PAGINE if v}
    for out, _, voce, g in PAGINE:
        if not voce:
            continue
        corrente = out == attivo or (g == "diritti" and gruppo == "diritti" and out == "diritti.html"
                                         and attivo not in principali)
        aria = ' aria-current="page"' if out == attivo else ""
        cls = ' class="attivo"' if corrente else ""
        voci.append(f'<li><a href="{out}"{cls}{aria}>{voce}</a></li>')
    return "\n".join(voci)


def sottomenu(attivo: str) -> str:
    voci = []
    for out, voce in SOTTOMENU_DIRITTI:
        aria = ' aria-current="page" class="attivo"' if out == attivo else ""
        voci.append(f'<li><a href="{out}"{aria}>{voce}</a></li>')
    return ('<nav class="sottomenu" aria-label="Sezioni della Bussola Diritti"><ul>'
            + "".join(voci) + "</ul></nav>")


MODELLO = """<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="{csp}">
<meta name="referrer" content="no-referrer">
<title>{titolo_pagina}</title>
<meta name="description" content="{descrizione}">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="style.css">
</head>
<body{classe_body}>
<a class="salta" href="#contenuto">Vai al contenuto</a>
<header class="testata">
  <div class="contenitore testata-riga">
    <a class="marchio" href="index.html">
      <img src="favicon.svg" alt="" width="36" height="36">
      <span><strong>Bilancia Civica</strong><br><em>Ogni decreto, pesato sulla tua vita</em></span>
    </a>
  </div>
  <nav class="menu" aria-label="Menu principale">
    <ul class="contenitore">
{menu}
    </ul>
  </nav>
</header>
<main id="contenuto" class="contenitore">
{sottomenu}
<article class="testo">
{corpo}
</article>
</main>
<footer class="piede">
  <div class="contenitore">
    <nav class="approfondire" aria-label="Per approfondire e trasparenza">
      <p><strong>Per approfondire:</strong> <a href="stato.html">Stato degli atti</a> · <a href="analisi-dl-190-2026.html">Analisi del decreto</a> · <a href="bussola-completa.html">Bussola, testo completo</a> · <a href="impatto.html">Simulatore (in sviluppo)</a> · <a href="alternative.html">Alternative (in preparazione)</a></p>
      <p><strong>Trasparenza:</strong> <a href="fonti.html">Fonti</a> · <a href="metodo.html">Metodo</a> · <a href="{repo}/blob/main/CORREZIONI.md" rel="noopener noreferrer">Registro correzioni</a> · <a href="contribuisci.html">Contribuisci</a></p>
    </nav>
    <p><strong>Contenuti informativi, non consulenza legale.</strong> Le fonti ufficiali restano il riferimento; per un caso concreto è opportuno rivolgersi a un avvocato, a un sindacato, a un patronato o a un'associazione di tutela dei diritti. <a href="note-legali.html">Note legali e privacy</a> · <a href="chi-siamo.html">Chi siamo e contatti</a></p>
    <p>Bilancia Civica è un progetto civico apartitico e open source. Testi aggiornati al {aggiornato}.
    <a href="{repo}/blob/main/LICENSE-TESTI" rel="noopener noreferrer">Testi CC BY-SA 4.0</a> (<a href="https://creativecommons.org/licenses/by-sa/4.0/deed.it" rel="noopener noreferrer">sintesi della licenza</a>) · <a href="{repo}/blob/main/LICENSE" rel="noopener noreferrer">Codice AGPL-3.0</a> · Testi normativi e citazioni di terzi esclusi: vedi <a href="note-legali.html#diritto-dautore-e-licenza">note legali</a>.<br>
    Hai trovato un errore? <a href="{repo}/issues" rel="noopener noreferrer">Segnalalo su GitHub</a> · <a href="{repo}" rel="noopener noreferrer">Codice sorgente</a> · <a href="metodo.html">Metodo</a></p>
    <p class="piccolo">Questo sito non usa cookie, non traccia i visitatori, non carica font o script esterni e non raccoglie dati.</p>
  </div>
</footer>
</body>
</html>
"""


# "In breve" per i documenti del repository (senza front matter): inserito solo nel sito,
# cosi' i file Markdown restano leggibili anche su GitHub.
INBREVE_DOC = {
    "docs/bussola-diritti.md": """- Riunirsi pacificamente e senz'armi, manifestare e scioperare sono diritti della Costituzione (artt. 17, 21 e 40). [FATTO · Alta]
- Questa è la versione completa, con tutte le norme e le fonti: per una lettura veloce c'è la panoramica [Diritti e regole](diritti.html).
- Il decreto sicurezza in vigore dal 23 ottobre 2026 è spiegato nel capitolo 5. Le parole tecniche sono nel [glossario](glossario.html).""",
    "docs/analisi-dl-190-2026.md": """- Analisi tecnica, articolo per articolo, del decreto sicurezza (decreto-legge n. 190 del 22 ottobre 2026) e scheda sugli aiuti all'autotrasporto. [FATTO · Alta]
- Per una sintesi semplice parti da [Decreto sicurezza](decreto.html); le parole tecniche sono nel [glossario](glossario.html).
- Revisione da parte di un giurista e di un economista indipendenti: **da fare**.""",
    "METODOLOGIA.md": """- Ogni affermazione ha un'etichetta (FATTO, STIMA, INTERPRETAZIONE, DA VERIFICARE) e un livello di certezza.
- Prima vengono le fonti ufficiali; le stime sono solo numeri, sempre come intervallo.
- Stessi criteri per tutti gli schieramenti, diritto di replica e correzioni pubbliche.""",
    "CONTRIBUTING.md": """- Chiunque può proporre correzioni con una segnalazione o una proposta di modifica su GitHub.
- Niente numeri inventati, sempre la fonte, le quattro etichette e nessun dato personale.""",
}

MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio",
        "agosto", "settembre", "ottobre", "novembre", "dicembre"]
SIGLE = [  # (forma nel testo, spiegazione) - solo la prima occorrenza per pagina
    ("D.L.", "decreto-legge"), ("d.lgs.", "decreto legislativo"), ("DPR", "decreto del Presidente della Repubblica"),
    ("c.p.p.", "codice di procedura penale"), ("c.p.", "codice penale"), ("Cost.", "Costituzione"),
    ("TULPS", "Testo unico delle leggi di pubblica sicurezza"), ("GU", "Gazzetta Ufficiale"),
    ("PM", "pubblico ministero"), ("TAR", "Tribunale amministrativo regionale"), ("CdM", "Consiglio dei ministri"),
    ("AC", "Atto Camera (numero del disegno di legge alla Camera)"), ("UPB", "Ufficio parlamentare di bilancio"),
    ("RGS", "Ragioneria Generale dello Stato"), ("MIT", "Ministero delle infrastrutture e dei trasporti"),
    ("MEF", "Ministero dell'economia e delle finanze"), ("ISTAT", "Istituto nazionale di statistica"),
    ("UE", "Unione europea"), ("L.", "legge"),
]
_NO_TESTO = {"a", "h1", "h2", "h3", "h4", "h5", "h6", "code", "pre", "abbr", "summary", "title"}


def rifinisci(corpo: str) -> str:
    """Nel solo testo visibile: date gg/mm/aaaa per esteso e prima occorrenza delle sigle in <abbr>."""
    viste: set = set()
    pila: list = []
    out = []
    for pezzo in re.split(r"(<[^>]+>)", corpo):
        if pezzo.startswith("<"):
            m = re.match(r"<(/?)([a-zA-Z0-9]+)", pezzo)
            if m:
                nome = m.group(2).lower()
                if m.group(1):
                    if nome in pila:
                        while pila and pila.pop() != nome:
                            pass
                elif nome in _NO_TESTO and not pezzo.endswith("/>"):
                    pila.append(nome)
            out.append(pezzo)
            continue
        if "code" in pila or "pre" in pila:
            out.append(pezzo)
            continue
        pezzo = re.sub(r"(?<![\d/])(\d{1,2})/(\d{1,2})/(\d{4})(?![\d/])",
                       lambda m: f"{int(m.group(1))} {MESI[int(m.group(2)) - 1]} {m.group(3)}"
                       if 1 <= int(m.group(2)) <= 12 and 1 <= int(m.group(1)) <= 31 else m.group(0), pezzo)
        if not any(x in pila for x in ("a", "h1", "h2", "h3", "h4", "h5", "h6", "code", "pre", "abbr", "summary")):
            for sigla, spieg in SIGLE:
                if sigla in viste:
                    continue
                pat = r"(?<![\w.])" + re.escape(sigla) + (r"(?= \d)" if sigla == "L." else r"(?![\w])")
                m = re.search(pat, pezzo)
                if m:
                    viste.add(sigla)
                    pezzo = (pezzo[:m.start()] + f'<abbr title="{html.escape(spieg)}">{sigla}</abbr>'
                             + pezzo[m.end():])
        out.append(pezzo)
    return "".join(out)


def costruisci() -> list[str]:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    for f in (ROOT / "static").iterdir():
        shutil.copy(f, OUT / f.name)
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    scritte = []
    for out, sorgente, _, gruppo in PAGINE:
        meta, testo = leggi(sorgente)
        if sorgente in INBREVE_DOC:
            m = re.search(r"^#\s+.+\n(?:###\s+.+\n)?", testo, re.M)
            blocco = "\n::: inbreve\n**In breve**\n\n" + INBREVE_DOC[sorgente] + "\n:::\n\n"
            if m:
                # il sottotitolo "###" subito dopo il titolo diventa un paragrafo (niente salto h1 -> h3)
                testa = re.sub(r"^###\s+(.+)$", lambda s: "*" + s.group(1).strip("* ") + "*", m.group(0), flags=re.M)
                testo = testa + blocco + testo[m.end():]
            else:
                testo = blocco + testo
        toc: list = []
        corpo = markdown(testo, toc)
        corpo = rifinisci(corpo)
        corpo = re.sub(r'((?:<div class="box box-funzione">.*?</div>\s*)+)',
                       lambda m: '<div class="griglia">' + m.group(1) + "</div>", corpo, flags=re.S)
        if meta.get("indice") == "si" and toc:
            indice = ('<nav class="indice" aria-label="In questa pagina"><p><strong>In questa pagina</strong></p><ul>'
                      + "".join(f'<li><a href="#{a}">{t}</a></li>' for a, t in toc) + "</ul></nav>")
            corpo = corpo.replace("<!--INDICE-->", "")
            primo_h2 = corpo.find("<h2")
            corpo = corpo[:primo_h2] + indice + corpo[primo_h2:] if primo_h2 >= 0 else corpo + indice
        if 'class="et et-' in corpo:
            corpo += ('<aside class="legenda" aria-label="Come leggere le etichette"><p><strong>Come leggere le etichette</strong></p><ul>'
                      + "".join(f'<li><span class="et et-{ETICHETTE[n]}">{n}</span> {html.escape(s)}</li>' for n, s in SPIEGAZIONE.items())
                      + '</ul><p>Alta, Media o Bassa indicano quanto è solida l\'informazione. <a href="glossario.html">Glossario</a> · <a href="metodo.html#13-etichette-fatto--stima--interpretazione--da-verificare">Metodo completo</a></p></aside>')
        titolo = meta.get("titolo", "Bilancia Civica")
        pagina = MODELLO.format(
            csp=CSP,
            titolo_pagina=html.escape(titolo if out == "index.html" else f"{titolo} · Bilancia Civica"),
            descrizione=html.escape(meta.get("descrizione", "Bilancia Civica: strumento civico apartitico e open source che spiega leggi e decreti con fonti verificabili.")),
            classe_body=' class="home"' if out == "index.html" else "",
            menu=menu(out, gruppo),
            sottomenu=sottomenu(out) if gruppo == "diritti" or out == "bussola-completa.html" else "",
            corpo=corpo,
            repo=REPO_URL,
            aggiornato=AGGIORNATO,
        )
        (OUT / out).write_text(pagina, encoding="utf-8")
        scritte.append(out)
    return scritte


if __name__ == "__main__":
    pagine = costruisci()
    print(f"Sito generato in {OUT.relative_to(ROOT)}/: {len(pagine)} pagine")
    for p in pagine:
        print("  ", p)
    sys.exit(0)
