# -*- coding: utf-8 -*-
"""Dati aperti di Bilancia Civica: estrae le affermazioni etichettate dalle pagine.

Usato da ``build.py``. Solo libreria standard di Python.

Le affermazioni non vengono copiate a mano: sono lette dall'HTML generato dagli
stessi file Markdown del sito, quindi testo, etichetta e collegamenti sono
sempre quelli pubblicati. Le regole di lettura sono descritte in ``DATI.md``.

Direttive facoltative nei file Markdown (righe di commento, invisibili sul sito):

    <!-- dati: esempio -->                il blocco seguente usa le etichette solo
                                          come esempio (legende): non è un'affermazione
    <!-- dati: intestazione -->           il blocco seguente è un'intestazione: la sua
                                          etichetta vale per i blocchi che seguono, fino
                                          al prossimo titolo o separatore
    <!-- dati: intestazione-precedente --> come sopra, ma per l'elenco o la tabella
                                          che precede
"""
from __future__ import annotations

import hashlib
import html
import json
import re
import unicodedata
from html.parser import HTMLParser
from urllib.parse import urlsplit

VERSIONE_SCHEMA = "1.0.0"
BASE_SITO = "https://bilanciacivica.github.io/bilancia-civica/"
ETICHETTE_VALIDE = ("FATTO", "STIMA", "INTERPRETAZIONE", "DA VERIFICARE")
RE_DIRETTIVA = re.compile(r"^<!--\s*dati:\s*([a-z-]+)\s*-->$")
DIRETTIVE = ("esempio", "intestazione", "intestazione-precedente")

# Siti istituzionali: una fonte su questi domini è marcata "ufficiale".
DOMINI_UFFICIALI = (
    "gazzettaufficiale.it", "normattiva.it", "camera.it", "senato.it", "governo.it",
    "cortecostituzionale.it", "gov.it", "cgsse.it", "upbilancio.it", "istat.it",
    "anac.it", "europa.eu", "quirinale.it",
)

# Atti citati spesso senza collegamento nel testo: testo ufficiale da collegare.
# Solo indirizzi istituzionali (Normattiva, Gazzetta Ufficiale, Corte costituzionale).
NIR = "https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:"
ATTI = {
    "Costituzione": ("Costituzione della Repubblica italiana", NIR + "costituzione:1947-12-27"),
    "Codice penale": ("Codice penale (R.D. 1398/1930)", NIR + "regio.decreto:1930-10-19;1398"),
    "Codice di procedura penale": ("Codice di procedura penale (DPR 447/1988)",
                                   NIR + "decreto.del.presidente.della.repubblica:1988-09-22;447"),
    "TULPS": ("Testo unico delle leggi di pubblica sicurezza (R.D. 773/1931)",
              NIR + "regio.decreto:1931-06-18;773"),
    "D.L. 190/2026": ("D.L. 22 ottobre 2026, n. 190 (testo in Gazzetta Ufficiale)",
                      "https://www.gazzettaufficiale.it/eli/id/2026/10/22/26G00214/SG"),
    "D.L. 193/2026": ("D.L. 23 ottobre 2026, n. 193 (testo in Gazzetta Ufficiale)",
                      "https://www.gazzettaufficiale.it/eli/id/2026/10/23/26G00216/SG"),
    "D.L. 23/2026": ("D.L. 24 febbraio 2026, n. 23 (testo in Gazzetta Ufficiale)",
                     "https://www.gazzettaufficiale.it/eli/id/2026/02/24/26G00042/SG"),
    "L. 54/2026": ("L. 24 aprile 2026, n. 54 (testo in Gazzetta Ufficiale)",
                   "https://www.gazzettaufficiale.it/eli/id/2026/04/24/26G00078/SG"),
    "D.L. 59/1978": ("D.L. 21 marzo 1978, n. 59", NIR + "decreto.legge:1978-03-21;59"),
    "D.L. 33/2026": ("D.L. 18 marzo 2026, n. 33", NIR + "decreto.legge:2026-03-18;33"),
    "L. 146/1990": ("L. 12 giugno 1990, n. 146", NIR + "legge:1990-06-12;146"),
    "L. 300/1970": ("L. 20 maggio 1970, n. 300 (Statuto dei lavoratori)", NIR + "legge:1970-05-20;300"),
    "L. 152/1975": ("L. 22 maggio 1975, n. 152", NIR + "legge:1975-05-22;152"),
    "L. 110/1975": ("L. 18 aprile 1975, n. 110", NIR + "legge:1975-04-18;110"),
    "L. 83/2000": ("L. 11 aprile 2000, n. 83", NIR + "legge:2000-04-11;83"),
    "L. 80/2025": ("L. 9 giugno 2025, n. 80", NIR + "legge:2025-06-09;80"),
    "d.lgs. 66/1948": ("D.lgs. 22 gennaio 1948, n. 66", NIR + "decreto.legislativo:1948-01-22;66"),
    "d.lgs. 159/2011": ("D.lgs. 6 settembre 2011, n. 159 (Codice antimafia e misure di prevenzione)",
                        NIR + "decreto.legislativo:2011-09-06;159"),
    "DPR 448/1988": ("DPR 22 settembre 1988, n. 448 (processo penale minorile)",
                     NIR + "decreto.del.presidente.della.repubblica:1988-09-22;448"),
}

# Tema: prima la pagina, poi parole chiave nella sezione e nel testo.
TEMA_PAGINA = {
    "presidio.html": "presidi", "corteo.html": "cortei", "sciopero.html": "sciopero",
    "decreto.html": "decreto-sicurezza", "esempio.html": "decreto-sicurezza",
}
TEMI_PAROLE = [
    ("autotrasporto", r"autotrasport|credito d.imposta|camionist|gasolio"),
    ("legge-di-bilancio", r"legge di bilancio|manovra 20\d\d|Documento programmatico di bilancio"),
    ("sciopero", r"scioper|L\. 146/1990|precettazion|astensione collettiva"),
    ("decreto-sicurezza", r"decreto sicurezza|D\.L\. 190|n\. 190\b|190/2026|420-bis|AC 3159"),
    ("presidi", r"presidi|riunion|preavviso|art\. 18 TULPS|art\. 17 Cost"),
    ("cortei", r"corte[oi]|manifestaz|scioglimento|fermo preventivo|travisament"),
]
TEMI = ["presidi", "cortei", "sciopero", "decreto-sicurezza", "autotrasporto",
        "legge-di-bilancio", "generale"]


def _norm(testo: str) -> str:
    t = html.unescape(testo).replace("\u00a0", " ")
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"\(\s*\)", "", t)
    t = re.sub(r"\s+([.,;:)\]])", r"\1", t)
    t = re.sub(r"([(\[])\s+", r"\1", t)
    t = t.strip(" ;,—–-").strip()
    t = re.sub(r"^[.:]\s*", "", t)
    return t


# ---------------------------------------------------------------------------
# Albero HTML minimo (con posizione di ogni tag di apertura)
# ---------------------------------------------------------------------------
VUOTI = {"br", "img", "hr", "meta", "link", "input", "wbr"}


class Nodo:
    __slots__ = ("tag", "attrs", "figli", "pos", "padre")

    def __init__(self, tag, attrs=None, pos=None, padre=None):
        self.tag, self.attrs, self.figli, self.pos, self.padre = tag, dict(attrs or {}), [], pos, padre

    def classi(self):
        return (self.attrs.get("class") or "").split()

    def elementi(self):
        return [f for f in self.figli if isinstance(f, Nodo) and f.tag not in ("#text", "#comment")]


class _Parser(HTMLParser):
    def __init__(self, sorgente: str):
        super().__init__(convert_charrefs=True)
        self.inizi_riga = [0]
        for m in re.finditer("\n", sorgente):
            self.inizi_riga.append(m.end())
        self.radice = Nodo("#radice")
        self.corrente = self.radice

    def _pos(self):
        riga, col = self.getpos()
        return self.inizi_riga[riga - 1] + col

    def handle_starttag(self, tag, attrs):
        n = Nodo(tag, attrs, self._pos(), self.corrente)
        self.corrente.figli.append(n)
        if tag not in VUOTI:
            self.corrente = n

    def handle_startendtag(self, tag, attrs):
        self.corrente.figli.append(Nodo(tag, attrs, self._pos(), self.corrente))

    def handle_endtag(self, tag):
        n = self.corrente
        while n is not self.radice and n.tag != tag:
            n = n.padre
        if n is not self.radice:
            self.corrente = n.padre

    def handle_data(self, data):
        t = Nodo("#text", padre=self.corrente)
        t.attrs["v"] = data
        self.corrente.figli.append(t)

    def handle_comment(self, data):
        c = Nodo("#comment", padre=self.corrente)
        c.attrs["v"] = data.strip()
        self.corrente.figli.append(c)


def _testo(n: Nodo) -> str:
    if n.tag == "#text":
        return n.attrs["v"]
    if n.tag == "#comment":
        return ""
    if n.tag == "br":
        return " "
    return "".join(_testo(f) for f in n.figli)


def _e_badge(n: Nodo) -> bool:
    return n.tag == "span" and "etichetta" in n.classi()


def _leggi_badge(n: Nodo) -> dict:
    nome, extra, link = "", "", []
    for f in n.elementi():
        if f.tag == "span" and "et" in f.classi():
            nome = _testo(f).strip()
        elif f.tag == "span" and "et-extra" in f.classi():
            extra = _testo(f)
            link = _link_in(f)
    extra = _norm(extra.strip(" ·,"))
    certezza = None
    m = re.match(r"^(?:certezza\s+)?(Alta|Media|Bassa)\b[\s,:·]*(.*)$", extra)
    if m:
        certezza, extra = m.group(1), m.group(2)
    return {"etichetta": nome, "certezza": certezza, "nota": _norm(extra) or None, "link": link, "nodo": n}


def _link_in(n: Nodo) -> list:
    out = []
    if n.tag == "a" and n.attrs.get("href"):
        out.append((n.attrs["href"], _norm(_testo(n))))
    for f in n.figli:
        if isinstance(f, Nodo) and f.tag not in ("#text", "#comment"):
            out.extend(_link_in(f))
    return out


def _sequenza(n: Nodo, escludi_liste: bool = True) -> list:
    """Linearizza un blocco: testi, collegamenti e badge in ordine."""
    seq: list = []

    def visita(x: Nodo):
        if x.tag == "#text":
            seq.append(("t", x.attrs["v"]))
            return
        if x.tag in ("#comment",):
            return
        if x.tag == "br":
            seq.append(("t", " "))
            return
        if escludi_liste and x is not n and x.tag in ("ul", "ol", "pre", "table", "div"):
            return
        if _e_badge(x):
            seq.append(("b", _leggi_badge(x)))
            return
        if x.tag == "a" and x.attrs.get("href"):
            seq.append(("a", (x.attrs["href"], _norm(_testo(x)))))
        if x.tag in ("td", "th") and x.padre is not None and x.padre.elementi() and x is not x.padre.elementi()[0]:
            seq.append(("t", " — "))
        for f in x.figli:
            visita(f)

    visita(n)
    return seq


# ---------------------------------------------------------------------------
# Riferimenti normativi (estrazione automatica dal testo)
# ---------------------------------------------------------------------------
_N = r"(\d+)"
_ANNO = r"(\d{4})"
_MESE = r"(?:gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre)"
RE_ATTI = [
    (re.compile(r"\bCost(?:ituzione|\.)"), lambda m: "Costituzione"),
    (re.compile(r"\bc\.p\.p\."), lambda m: "Codice di procedura penale"),
    (re.compile(r"\bc\.p\.(?!p)"), lambda m: "Codice penale"),
    (re.compile(r"\bTULPS\b"), lambda m: "TULPS"),
    (re.compile(r"\b(?:D\.L\.|decreto-legge)\s+(?:n\.\s*)?" + _N + "/" + _ANNO), lambda m: f"D.L. {m.group(1)}/{m.group(2)}"),
    (re.compile(r"\b(?:D\.L\.|decreto-legge)\s+\d{1,2}\s+" + _MESE + r"\s+" + _ANNO + r",\s*n\.\s*" + _N),
     lambda m: f"D.L. {m.group(2)}/{m.group(1)}"),
    (re.compile(r"\bdecreto-legge\s+n\.\s*" + _N + r"\s+del\s+\d{1,2}\s+" + _MESE + r"\s+" + _ANNO),
     lambda m: f"D.L. {m.group(1)}/{m.group(2)}"),
    (re.compile(r"(?<![\w.-])(?:L\.|legge)\s+(?:n\.\s*)?" + _N + "/" + _ANNO), lambda m: f"L. {m.group(1)}/{m.group(2)}"),
    (re.compile(r"(?<![\w.-])(?:L\.|legge)\s+\d{1,2}\s+" + _MESE + r"\s+" + _ANNO + r",\s*n\.\s*" + _N),
     lambda m: f"L. {m.group(2)}/{m.group(1)}"),
    (re.compile(r"\bd\.\s?lgs\.\s+(?:n\.\s*)?" + _N + "/" + _ANNO, re.I), lambda m: f"d.lgs. {m.group(1)}/{m.group(2)}"),
    (re.compile(r"\bD\.?P\.?R\.?\s+(?:n\.\s*)?" + _N + "/" + _ANNO), lambda m: f"DPR {m.group(1)}/{m.group(2)}"),
    (re.compile(r"\bR\.D\.\s+773/1931"), lambda m: "TULPS"),
]
RE_ART = re.compile(
    r"\b[Aa]rtt?\.\s*(\d+(?:[-‑](?:bis|ter|quater|quinquies|sexies|septies|octies|novies|decies))?(?:\.\d+)?"
    r"(?:(?:\s*,\s*|\s+e\s+)\d+(?:[-‑](?:bis|ter|quater))?(?:\.\d+)?)*)")
RE_SENT = re.compile(r"\b(?:Corte cost(?:ituzionale|\.)?(?:\s+(?:sent(?:enza|\.)\s*)?n?\.?\s*)?|sent(?:enza|enze|\.)\s+(?:n\.\s*)?)"
                     r"(\d{1,4})/(\d{4})((?:\s+e\s+\d{1,4}/\d{4})*)")


def _atti_in(testo: str) -> list:
    trovati = []
    for rx, nome in RE_ATTI:
        for m in rx.finditer(testo):
            trovati.append((m.start(), m.end(), nome(m), m.group(0)))
    trovati.sort()
    return trovati


def riferimenti(testo: str, contesto: str | None = None) -> list:
    """Riferimenti normativi citati nel testo. Un articolo senza atto prende l'atto dell'intestazione
    (contesto) solo se l'intestazione ne cita uno soltanto e il testo nessuno."""
    atti = _atti_in(testo)
    atto_predefinito = None
    if contesto and not atti:
        nel_contesto = {nome for _, _, nome, _ in _atti_in(contesto)}
        if len(nel_contesto) == 1:
            atto_predefinito = nel_contesto.pop()
    rif: list = []
    usati: set = set()
    for m in RE_ART.finditer(testo):
        # atto citato subito dopo l'articolo (entro 45 caratteri, senza un nuovo «art.» in mezzo)
        atto = None
        for s, e, nome, _ in atti:
            if m.end() <= s <= m.end() + 45 and not RE_ART.search(testo[m.end():s]) and ";" not in testo[m.end():s]:
                atto, fine = nome, e
                usati.add((s, e))
                break
        citazione = testo[m.start():fine] if atto else m.group(0)
        if not atto:
            # atto citato subito prima, come in «Costituzione (artt. 17, 21 e 40)»
            for s, e, nome, _ in atti:
                if 0 <= m.start() - e <= 3:
                    atto = nome
                    break
        if not atto and atto_predefinito:
            atto = atto_predefinito
        for numero in re.split(r"\s*,\s*|\s+e\s+", m.group(1)):
            if numero:
                rif.append({"citazione": _norm(citazione), "atto": atto, "articolo": numero.replace("‑", "-")})
    for s, e, nome, cit in atti:
        if (s, e) not in usati:
            rif.append({"citazione": _norm(cit), "atto": nome, "articolo": None})
    for m in RE_SENT.finditer(testo):
        numeri = [(m.group(1), m.group(2))] + re.findall(r"(\d{1,4})/(\d{4})", m.group(3) or "")
        for n, a in numeri:
            rif.append({"citazione": _norm(m.group(0)), "atto": f"Corte cost. {int(n)}/{a}", "articolo": None})
    # dedup stabile
    visti, out = set(), []
    for r in rif:
        k = (r["atto"], r["articolo"])
        if k in visti:
            continue
        visti.add(k)
        out.append(r)
    # un atto senza articolo è superfluo se lo stesso atto compare con un articolo
    con_art = {r["atto"] for r in out if r["articolo"]}
    out = [r for r in out if r["articolo"] or r["atto"] not in con_art]
    return sorted(out, key=lambda r: ((r["atto"] or "~"), _chiave_art(r["articolo"])))


def _chiave_art(a):
    if not a:
        return (0, 0, "")
    m = re.match(r"(\d+)(.*)", a)
    return (1, int(m.group(1)), m.group(2)) if m else (2, 0, a)


def _url_atto(atto: str | None):
    if not atto:
        return None
    if atto in ATTI:
        return ATTI[atto]
    m = re.match(r"Corte cost\. (\d+)/(\d{4})$", atto)
    if m:
        return (f"Corte costituzionale, sentenza n. {m.group(1)}/{m.group(2)}",
                f"https://www.cortecostituzionale.it/scheda-pronuncia/{m.group(2)}/{m.group(1)}")
    return None


def ufficiale(url: str) -> bool:
    host = (urlsplit(url).hostname or "").lower()
    return any(host == d or host.endswith("." + d) for d in DOMINI_UFFICIALI)


# ---------------------------------------------------------------------------
# Estrazione
# ---------------------------------------------------------------------------
BREVE = 60


class Estrattore:
    def __init__(self, pagina: str, titolo: str, aggiornato_iso: str):
        self.pagina, self.titolo, self.aggiornato = pagina, titolo, aggiornato_iso
        self.affermazioni: list = []
        self.badge_esempio = 0
        self.badge_intestazione = 0
        self.sezione = None   # ultimo titolo h2 o h3
        self.capitolo = None  # ultimo titolo h2

    # -- utilità ----------------------------------------------------------
    def _tema(self, testo: str) -> str:
        if self.pagina in TEMA_PAGINA:
            return TEMA_PAGINA[self.pagina]
        for fonte in (self.sezione or "", self.capitolo or "", testo):
            # vince il tema citato per primo nel testo
            trovati = [(m.start(), k, tema) for k, (tema, rx) in enumerate(TEMI_PAROLE)
                       for m in [re.search(rx, fonte, re.I)] if m]
            if trovati:
                return min(trovati)[2]
        return "generale"

    def _nuova(self, testo, badge, nodo_ancora, link, contesto=None, ereditata=False):
        testo = _norm(testo)
        if not testo:
            return
        contesto = _norm(contesto) if contesto else None
        fonti, viste = [], set()
        for href, titolo in link:
            if href.startswith(("http://", "https://")) and href not in viste:
                viste.add(href)
                fonti.append({"titolo": titolo or href, "url": href, "ufficiale": ufficiale(href),
                              "origine": "collegamento nel testo"})
        rif = riferimenti(testo, contesto)
        if contesto:  # anche gli atti citati nell'intestazione o nel testo vicino
            gia = {(r["atto"], r["articolo"]) for r in rif}
            atti_con_art = {r["atto"] for r in rif if r["articolo"]}
            for r in riferimenti(contesto):
                if (r["atto"], r["articolo"]) in gia or (r["articolo"] is None and r["atto"] in atti_con_art):
                    continue
                rif.append(r)
            rif.sort(key=lambda r: ((r["atto"] or "~"), _chiave_art(r["articolo"])))
        for r in rif:
            u = _url_atto(r["atto"])
            if u and u[1] not in viste:
                viste.add(u[1])
                fonti.append({"titolo": u[0], "url": u[1], "ufficiale": True,
                              "origine": "riferimento normativo citato"})
        self.affermazioni.append({
            "testo": testo, "etichetta": badge["etichetta"], "certezza": badge["certezza"],
            "nota_etichetta": badge["nota"], "etichetta_ereditata": ereditata,
            "contesto": contesto, "tema": self._tema(testo + " " + (contesto or "")),
            "sezione": self.sezione, "riferimenti_normativi": rif, "fonti": fonti,
            "_nodo": nodo_ancora,
        })

    # -- blocchi ----------------------------------------------------------
    def contenitore(self, nodo: Nodo, ereditata=None):
        figli = [f for f in nodo.figli if f.tag != "#text" or f.attrs["v"].strip()]
        elementi = [f for f in figli if f.tag not in ("#text", "#comment")]
        direttiva = None
        consumati: set = set()
        precedente = None
        introduzione = None  # paragrafo senza etichetta che finisce con «:» e introduce un elenco
        for f in figli:
            if f.tag == "#comment":
                m = re.match(r"^dati:\s*([a-z-]+)$", f.attrs["v"])
                if m:
                    direttiva = m.group(1)
                    if direttiva not in DIRETTIVE:
                        raise ValueError(f"{self.pagina}: direttiva sconosciuta {direttiva!r}")
                continue
            if f.tag == "#text":
                continue
            if id(f) in consumati:
                precedente = f
                continue
            i = elementi.index(f)
            successivo = elementi[i + 1] if i + 1 < len(elementi) else None
            if direttiva == "esempio":
                self.badge_esempio += len(_badge_in(f))
            elif direttiva == "intestazione":
                # l'etichetta vale per tutti i blocchi seguenti, fino al prossimo titolo o separatore
                bersagli = []
                for g in elementi[i + 1:]:
                    if g.tag in ("h1", "h2", "h3", "h4", "h5", "h6", "hr"):
                        break
                    bersagli.append(g)
                if not bersagli or not _badge_in(f):
                    raise ValueError(f"{self.pagina}: intestazione senza etichetta o senza bersaglio")
                self._intestazione(f, bersagli, ereditata)
                consumati.update(id(g) for g in bersagli)
            elif direttiva == "intestazione-precedente":
                if precedente is None or not _badge_in(f):
                    raise ValueError(f"{self.pagina}: intestazione senza etichetta o senza bersaglio")
                self._rimuovi_da(precedente)
                self._intestazione(f, [precedente], ereditata)
            else:
                if f.tag in ("ul", "ol") and introduzione and not ereditata:
                    usato = self.elemento(f, successivo, {"badge": None, "contesto": introduzione, "link": []})
                else:
                    usato = self.elemento(f, successivo, ereditata)
                if usato is not None:
                    consumati.add(id(usato))
            introduzione = None
            if f.tag == "p" and not _badge_in(f) and _norm(_testo(f)).endswith(":"):
                introduzione = _norm(_testo(f))
            direttiva = None
            precedente = f

    def _rimuovi_da(self, bersaglio: Nodo):
        def dentro(n):
            while n is not None:
                if n is bersaglio:
                    return True
                n = n.padre
            return False
        self.affermazioni = [a for a in self.affermazioni if not dentro(a["_nodo"])]

    def elemento(self, f: Nodo, successivo, ereditata):
        """Ritorna l'elemento successivo se è stato consumato come bersaglio di un'intestazione."""
        tag = f.tag
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            if tag in ("h2", "h3"):
                self.sezione = _norm(_testo(f))
                if tag == "h2":
                    self.capitolo = self.sezione
            if _badge_in(f):
                return self.blocco(f, None, None)
            return None
        if tag in ("p", "summary"):
            return self.blocco(f, successivo, ereditata)
        if tag in ("ul", "ol"):
            for li in f.elementi():
                if li.tag == "li":
                    self.voce(li, ereditata)
            return None
        if tag == "table":
            self.tabella(f, ereditata)
            return None
        if tag == "pre":
            return None
        if tag in ("div", "details", "blockquote", "nav", "aside", "section", "article", "thead", "tbody"):
            if tag == "nav" and "indice" in f.classi():
                return None
            self.contenitore(f, ereditata if (ereditata and ereditata.get("badge")) else None)
            return None
        if _badge_in(f):
            return self.blocco(f, successivo, ereditata)
        return None

    def tabella(self, t: Nodo, ereditata):
        for parte in t.elementi():
            righe = parte.elementi() if parte.tag in ("thead", "tbody") else [parte]
            for tr in righe:
                if tr.tag != "tr":
                    continue
                if parte.tag == "thead":
                    if _badge_in(tr):
                        self.blocco(tr, None, None)
                    continue
                self.blocco(tr, None, ereditata)

    def voce(self, li: Nodo, ereditata):
        liste = [x for x in li.elementi() if x.tag in ("ul", "ol")]
        altri = [x for x in li.elementi() if x.tag in ("pre", "table", "div")]
        bersaglio = liste[0] if liste else None
        usato = self.blocco(li, bersaglio, ereditata)
        sotto = ereditata if (ereditata and ereditata.get("badge")) else None
        for sub in liste:
            if sub is usato:
                continue
            for sli in sub.elementi():
                if sli.tag == "li":
                    self.voce(sli, sotto)
        for x in altri:
            self.elemento(x, None, sotto)

    def _intestazione(self, testa: Nodo, bersagli: list, ereditata_sopra):
        seq = _sequenza(testa)
        badge = [x[1] for x in seq if x[0] == "b"]
        self.badge_intestazione += len(badge)
        # nel contesto l'etichetta dell'intestazione resta visibile, in forma [ETICHETTA · Certezza]
        contesto = _norm("".join(
            x[1] if x[0] == "t" else
            ("[" + x[1]["etichetta"] + (" · " + x[1]["certezza"] if x[1]["certezza"] else "") + "]" if x[0] == "b" else "")
            for x in seq))
        link = [x[1] for x in seq if x[0] == "a"] + [l for b in badge for l in b["link"]]
        if ereditata_sopra and ereditata_sopra.get("contesto"):
            contesto = _norm(ereditata_sopra["contesto"] + " " + contesto)
        ered = {"badge": badge[0], "contesto": contesto or None, "link": link}
        for bersaglio in bersagli:
            if bersaglio.tag in ("ul", "ol"):
                for li in bersaglio.elementi():
                    if li.tag == "li":
                        self.voce(li, ered)
            elif bersaglio.tag == "table" or (bersaglio.tag == "div" and "tabella" in bersaglio.classi()):
                t = bersaglio if bersaglio.tag == "table" else next(x for x in bersaglio.elementi() if x.tag == "table")
                self.tabella(t, ered)
            elif bersaglio.tag == "p":
                self.blocco(bersaglio, None, ered)
            else:
                self.contenitore(bersaglio, ered)

    def blocco(self, b: Nodo, successivo, ereditata):
        seq = _sequenza(b)
        parti: list = [{"t": "", "a": []}]
        badge: list = []
        for tipo, v in seq:
            if tipo == "b":
                badge.append(v)
                parti.append({"t": "", "a": []})
            elif tipo == "t":
                parti[-1]["t"] += v
            else:
                parti[-1]["a"].append(v)
        grezzi = [p["t"] for p in parti]
        testi = [_norm(t) for t in grezzi]
        tutto = _norm(" ".join(grezzi))
        tutti_link = [l for p in parti for l in p["a"]]
        prima_cella = None
        if b.tag == "tr":
            celle = [c for c in b.elementi() if c.tag in ("td", "th")]
            prima_cella = _norm(_testo(celle[0])) if celle else None
        eredita = ereditata if (ereditata and ereditata.get("badge")) else None
        intro = ereditata["contesto"] if (ereditata and not ereditata.get("badge")) else None
        if not badge:
            if eredita:
                if _ha_nota(b):
                    return None  # nota redazionale: non è un'affermazione etichettata
                if b.tag == "p" and len(tutto) <= 40 and len(b.elementi()) == 1 and b.elementi()[0].tag in ("em", "strong") \
                        and _norm(_testo(b.elementi()[0])) == tutto:
                    return None  # sottotitolo in corsivo o grassetto
                self._nuova(tutto, eredita["badge"], b, tutti_link + eredita["link"], eredita["contesto"], True)
            return None
        # Intestazione: etichetta da sola, oppure testo breve o che finisce con «:», seguito da elenco o tabella
        e_lista = successivo is not None and (
            successivo.tag in ("ul", "ol", "table") or (successivo.tag == "div" and "tabella" in successivo.classi()))
        solo_fine = all(not t for t in testi[1:])
        if e_lista and len(badge) == 1 and (not tutto or (solo_fine and len(testi[0]) <= BREVE) or tutto.endswith(":")):
            self._intestazione(b, [successivo], ereditata if eredita else None)
            if len(tutto) > 2 * BREVE:  # intestazione lunga: è anche un'affermazione a sé
                self._nuova(tutto, badge[0], badge[0]["nodo"], tutti_link + badge[0]["link"])
                self.badge_intestazione -= 1
            return successivo
        if not tutto:
            raise ValueError(f"{self.pagina}: etichetta isolata senza testo e senza elenco: {_testo(b)[:80]!r}")
        # Divisione per etichette
        consumato = [False] * len(testi)
        uscite = []
        for k, bd in enumerate(badge, start=1):
            prima = testi[k - 1] if not consumato[k - 1] else ""
            dopo = testi[k]
            link_prima = parti[k - 1]["a"] if not consumato[k - 1] else []
            ctx = None
            introduce = grezzi[k].lstrip().startswith((":", "—", "–", "- "))
            if not prima and dopo:
                testo, link = dopo, parti[k]["a"]
                consumato[k] = True
            elif prima and dopo and len(prima) <= BREVE and (introduce or not re.search(r"[.!?»)]$", prima)):
                testo, link = grezzi[k - 1] + grezzi[k], link_prima + parti[k]["a"]
                consumato[k - 1] = consumato[k] = True
            elif bd["etichetta"] == "DA VERIFICARE" and dopo:
                testo, link, ctx = dopo, parti[k]["a"] + link_prima, (prima or None)
                consumato[k - 1] = consumato[k] = True
            else:
                testo, link = prima, link_prima
                consumato[k - 1] = True
            uscite.append([testo, bd, link + bd["link"], ctx])
        # testo finale senza etichetta propria: diventa contesto dell'ultima affermazione
        coda = testi[-1]
        if not consumato[-1] and coda and uscite and not coda.startswith("→"):
            u = uscite[-1]
            u[3] = _norm((u[3] + " " if u[3] else "") + "Testo seguente, senza etichetta propria: " + coda)
            u[2] = u[2] + parti[-1]["a"]
        for testo, bd, link, ctx in uscite:
            if not _norm(testo):
                testo = tutto
            if prima_cella and not _norm(testo).startswith(prima_cella) and not (ctx and prima_cella in ctx):
                ctx = _norm(("Riga: " + prima_cella) + (". " + ctx if ctx else ""))
            for sopra in ((eredita or {}).get("contesto"), intro):
                if sopra:
                    ctx = _norm(sopra + (" " + ctx if ctx else ""))
            self._nuova(testo, bd, bd["nodo"], link + (eredita["link"] if eredita else []), ctx)
        return None


def _ha_nota(n: Nodo) -> bool:
    if n.tag == "span" and "et-nota" in n.classi():
        return True
    return any(_ha_nota(f) for f in n.figli if isinstance(f, Nodo) and f.tag not in ("#text", "#comment")
               and f.tag not in ("ul", "ol"))


def _badge_in(n: Nodo) -> list:
    out = []
    if _e_badge(n):
        return [n]
    for f in n.figli:
        if isinstance(f, Nodo) and f.tag not in ("#text", "#comment"):
            out.extend(_badge_in(f))
    return out


def _id(pagina: str, testo: str, etichetta: str, usati: set) -> str:
    base = re.sub(r"\.html$", "", pagina)
    base = "home" if base == "index" else base
    norm = unicodedata.normalize("NFKC", testo).casefold()
    norm = re.sub(r"[^\w]+", " ", norm).strip()
    h = hashlib.sha256(f"{etichetta}|{norm}".encode("utf-8")).hexdigest()[:10]
    ident = f"{base}-{h}"
    n = 2
    while ident in usati:
        ident = f"{base}-{h}-{n}"
        n += 1
    usati.add(ident)
    return ident


def estrai(corpo: str, pagina: str, titolo: str, aggiornato_iso: str, usati: set):
    """Ritorna (corpo con le ancore, affermazioni, conteggi di controllo)."""
    p = _Parser(corpo)
    p.feed(corpo)
    p.close()
    e = Estrattore(pagina, titolo, aggiornato_iso)
    e.contenitore(p.radice)
    inserimenti = []
    afferm = []
    nodi_usati = set()
    for a in e.affermazioni:
        nodo = a.pop("_nodo")
        if a["etichetta"] not in ETICHETTE_VALIDE:
            raise ValueError(f"{pagina}: etichetta non valida {a['etichetta']!r}")
        ident = _id(pagina, a["testo"], a["etichetta"], usati)
        if id(nodo) in nodi_usati:
            raise ValueError(f"{pagina}: due affermazioni sullo stesso elemento: {a['testo'][:60]!r}")
        nodi_usati.add(id(nodo))
        if "id" in nodo.attrs:
            raise ValueError(f"{pagina}: elemento con id già presente")
        inserimenti.append((nodo.pos + 1 + len(nodo.tag), ident))
        a = {"id": ident, **a, "pagina": {"url": f"{BASE_SITO}{pagina}#af-{ident}", "titolo": titolo,
                                          "sezione": a.pop("sezione")},
             "senza_fonte_collegata": not a["fonti"], "data_aggiornamento": aggiornato_iso}
        afferm.append(a)
    for pos, ident in sorted(inserimenti, reverse=True):
        corpo = corpo[:pos] + f' id="af-{ident}"' + corpo[pos:]
    corpo = re.sub(r"<!--\s*dati:\s*[a-z-]+\s*-->\n?", "", corpo)
    totale_badge = len(re.findall(r'<span(?: id="[^"]*")? class="etichetta"', corpo))
    controllo = {"badge": totale_badge, "esempio": e.badge_esempio, "intestazione": e.badge_intestazione,
                 "affermazioni": len(afferm)}
    return corpo, afferm, controllo


# ---------------------------------------------------------------------------
# File JSON
# ---------------------------------------------------------------------------
def scrivi_json(percorso, dati) -> None:
    percorso.write_text(json.dumps(dati, ensure_ascii=False, indent=2, sort_keys=False) + "\n", encoding="utf-8")


ORDINE_CAMPI = ["id", "testo", "etichetta", "certezza", "nota_etichetta", "etichetta_ereditata", "contesto",
                "tema", "pagina", "riferimenti_normativi", "fonti", "senza_fonte_collegata", "data_aggiornamento"]


def ordina_campi(a: dict) -> dict:
    return {k: a[k] for k in ORDINE_CAMPI}
