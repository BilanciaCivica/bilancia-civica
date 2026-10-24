#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
"""Bilancia Civica – server MCP locale (stdio), in sola lettura.

Legge i dati aperti pubblicati da Bilancia Civica (tre file JSON a indirizzi fissi),
li tiene in una cache locale e risponde a 5 strumenti. Solo libreria standard di Python.

- Sola lettura: nessuno strumento scrive, invia o modifica qualcosa.
- Nessuna telemetria: le domande non vengono registrate né inviate; l'unico traffico di rete
  sono le richieste GET dei file JSON pubblici, solo HTTPS.
- Modalità offline: BILANCIA_OFFLINE=1 (oppure --offline) usa solo la cache, senza rete.
- BILANCIA_DATI_DIR=<cartella> legge i file da una cartella locale (per esempio ``_site/dati``).

Uso: python3 bilancia_civica_mcp.py [--offline]
Licenza: GNU AGPL-3.0-only. Contenuti informativi, non consulenza legale.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import unicodedata
import urllib.request
from pathlib import Path

VERSIONE = "1.0.0"
BASE = "https://bilanciacivica.github.io/bilancia-civica/dati/"
FILE = ("indice.json", "affermazioni.json", "fonti.json")
TTL = 6 * 3600
MAX_BYTES = 5 * 1024 * 1024
PROTOCOLLI = ("2025-06-18", "2025-03-26", "2024-11-05")
ETICHETTE = ("FATTO", "STIMA", "INTERPRETAZIONE", "DA VERIFICARE")
AVVERTENZA = ("Contenuti informativi, non consulenza legale. Riporta sempre etichetta e fonte: "
              "un'affermazione DA VERIFICARE non è un fatto.")
RE_ID = re.compile(r"^[a-z0-9-]{1,80}$")
RE_TEMA = re.compile(r"^[a-z0-9-]{1,40}$")


def _log(msg: str) -> None:
    print(f"bilancia-civica-mcp: {msg}", file=sys.stderr, flush=True)


def offline() -> bool:
    return os.environ.get("BILANCIA_OFFLINE", "") not in ("", "0") or "--offline" in sys.argv[1:]


def _cache_dir() -> Path:
    base = os.environ.get("XDG_CACHE_HOME") or os.path.join(Path.home(), ".cache")
    p = Path(base) / "bilancia-civica-mcp"
    p.mkdir(parents=True, exist_ok=True)
    return p


class DatiNonDisponibili(OSError):
    """Errore con un messaggio sicuro da mostrare."""


def _leggi(dati: bytes) -> dict:
    if len(dati) > MAX_BYTES:
        raise ValueError("file troppo grande")
    obj = json.loads(dati.decode("utf-8"))
    if not isinstance(obj, dict):
        raise ValueError("formato dei dati non valido")
    return obj


def _scarica(nome: str) -> tuple[dict, bool]:
    """Restituisce (dati, da_cache). Indirizzo fisso, solo HTTPS, nessun parametro."""
    if nome not in FILE:
        raise ValueError("file non previsto")
    locale = os.environ.get("BILANCIA_DATI_DIR")
    if locale:
        return _leggi(Path(locale, nome).read_bytes()), False
    cache = _cache_dir() / nome
    if offline():
        if not cache.exists():
            raise DatiNonDisponibili("modalità offline senza cache: avvia una volta il server con la rete.")
        return _leggi(cache.read_bytes()), True
    if cache.exists() and time.time() - cache.stat().st_mtime < TTL:
        return _leggi(cache.read_bytes()), True
    req = urllib.request.Request(BASE + nome, headers={"User-Agent": f"bilancia-civica-mcp/{VERSIONE}"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            dati = r.read(MAX_BYTES + 1)
        obj = _leggi(dati)
        tmp = cache.with_suffix(".tmp")
        tmp.write_bytes(dati)
        tmp.replace(cache)
        return obj, False
    except (OSError, ValueError) as e:  # rete assente o risposta non valida: usa la cache, se c'è
        if cache.exists():
            _log(f"dati in rete non disponibili ({type(e).__name__}), uso la cache")
            return _leggi(cache.read_bytes()), True
        raise DatiNonDisponibili(f"dati non disponibili ({type(e).__name__}) e nessuna cache.") from e


class Dati:
    def __init__(self) -> None:
        self._caricato = 0.0

    def carica(self) -> None:
        if self._caricato and time.time() - self._caricato < TTL:
            return
        (indice, c1), (a, c2), (f, c3) = (_scarica(n) for n in FILE)
        if str(a.get("versione_schema", "")).split(".")[0] != "1":
            raise ValueError("versione dei dati non supportata")
        self.indice = indice
        self.affermazioni = a["affermazioni"]
        self.per_id = {x["id"]: x for x in self.affermazioni}
        self.temi = sorted({x["tema"] for x in self.affermazioni})
        self.fonti = f
        self.da_cache = c1 or c2 or c3
        self._caricato = time.time()

    def meta(self) -> dict:
        lic = self.indice["licenza"]
        return {
            "avvertenza": AVVERTENZA,
            "fonte_dati": BASE + "affermazioni.json",
            "attribuzione": lic["attribuzione"],
            "licenza_testi": lic["testi"],
            "generato_il": self.indice["generato_il"],
            "dati_da_cache": self.da_cache,
        }


D = Dati()


def _piega(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.casefold())
    return "".join(c for c in s if not unicodedata.combining(c))


def _sintesi(a: dict) -> dict:
    return {
        "id": a["id"],
        "testo": a["testo"],
        "etichetta": a["etichetta"],
        "certezza": a["certezza"],
        "tema": a["tema"],
        "riferimenti_normativi": a["riferimenti_normativi"],
        "fonti": a["fonti"],
        "senza_fonte_collegata": a["senza_fonte_collegata"],
        "pagina": a["pagina"]["url"],
    }


# --- validazione degli argomenti -------------------------------------------------------------
def _ammessi(args: dict, chiavi: tuple) -> None:
    extra = sorted(set(args) - set(chiavi))
    if extra:
        raise ValueError(f"argomenti non previsti: {', '.join(extra)}")


def _stringa(args: dict, k: str, maxlen: int, obbl: bool = False) -> str | None:
    v = args.get(k)
    if v is None or v == "":
        if obbl:
            raise ValueError(f"'{k}' è obbligatorio")
        return None
    if not isinstance(v, str) or len(v) > maxlen:
        raise ValueError(f"'{k}' non valido (testo di al massimo {maxlen} caratteri)")
    return v


def _id(args: dict) -> dict:
    i = _stringa(args, "id", 80, obbl=True)
    if not RE_ID.match(i):
        raise ValueError("'id' non valido: solo lettere minuscole, cifre e trattini")
    if i not in D.per_id:
        raise ValueError(f"id non trovato: {i}")
    return D.per_id[i]


# --- strumenti --------------------------------------------------------------------------------
def t_cerca(args: dict) -> dict:
    _ammessi(args, ("testo", "tema", "etichetta", "limite"))
    testo = _stringa(args, "testo", 200)
    tema = _stringa(args, "tema", 40)
    et = _stringa(args, "etichetta", 20)
    if et and et not in ETICHETTE:
        raise ValueError(f"etichetta non valida: usa {', '.join(ETICHETTE)}")
    if tema and (not RE_TEMA.match(tema) or tema not in D.temi):
        raise ValueError(f"tema non valido: usa {', '.join(D.temi)}")
    lim = args.get("limite", 10)
    if isinstance(lim, bool) or not isinstance(lim, int) or not 1 <= lim <= 50:
        raise ValueError("'limite' deve essere un numero intero tra 1 e 50")
    parole = _piega(testo).split() if testo else []
    out = []
    for a in D.affermazioni:
        if tema and a["tema"] != tema:
            continue
        if et and a["etichetta"] != et:
            continue
        if parole:
            h = _piega(a["testo"] + " " + (a.get("contesto") or ""))
            if not all(p in h for p in parole):
                continue
        out.append(_sintesi(a))
    return {"totale": len(out), "risultati": out[:lim], **D.meta()}


def t_get(args: dict) -> dict:
    _ammessi(args, ("id",))
    return {"affermazione": _id(args), **D.meta()}


def t_temi(args: dict) -> dict:
    _ammessi(args, ())
    c = D.indice["conteggi"]
    return {"temi": c["per_tema"], "per_etichetta": c["per_etichetta"],
            "etichette": D.indice["etichette"], **D.meta()}


def t_fonti(args: dict) -> dict:
    _ammessi(args, ("id",))
    a = _id(args)
    r = {
        "id": a["id"],
        "testo": a["testo"],
        "etichetta": a["etichetta"],
        "certezza": a["certezza"],
        "fonti": a["fonti"],
        "riferimenti_normativi": a["riferimenti_normativi"],
        "senza_fonte_collegata": a["senza_fonte_collegata"],
        "pagina": a["pagina"]["url"],
    }
    if a["senza_fonte_collegata"]:
        r["nota"] = ("Nessun link alla fonte per questa affermazione: cercala nella stessa sezione "
                     "della pagina o nell'elenco delle fonti del sito.")
    return {**r, **D.meta()}


def t_info(args: dict) -> dict:
    _ammessi(args, ())
    i = D.indice
    return {k: i[k] for k in ("progetto", "sito", "repository", "documentazione", "versione_schema",
                              "generato_il", "licenza", "etichette")} | {
        "conteggi": i["conteggi"],
        "server": f"bilancia-civica-mcp {VERSIONE} (sola lettura, nessuna telemetria)",
        **D.meta()}


_ID = {"type": "object", "properties": {"id": {"type": "string", "maxLength": 80, "pattern": "^[a-z0-9-]+$",
                                               "description": "codice dell'affermazione, per esempio presidio-abc0d7d83d"}},
       "required": ["id"], "additionalProperties": False}
_VUOTO = {"type": "object", "properties": {}, "additionalProperties": False}
_RO = {"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False, "destructiveHint": False}
TOOLS = {
    "cerca_affermazioni": (t_cerca, "Cerca affermazioni del sito Bilancia Civica per parole, tema o etichetta. "
                           "Ogni risultato riporta etichetta, certezza, fonti e pagina.", {
        "type": "object", "additionalProperties": False, "properties": {
            "testo": {"type": "string", "maxLength": 200, "description": "parole da cercare (devono esserci tutte)"},
            "tema": {"type": "string", "maxLength": 40, "description": "tema, vedi elenca_temi"},
            "etichetta": {"type": "string", "enum": list(ETICHETTE)},
            "limite": {"type": "integer", "minimum": 1, "maximum": 50, "default": 10}}}),
    "get_affermazione": (t_get, "Restituisce un'affermazione completa, dato il suo id.", _ID),
    "elenca_temi": (t_temi, "Elenca i temi con il numero di affermazioni e i conteggi per etichetta.", _VUOTO),
    "fonti_di": (t_fonti, "Fonti e riferimenti normativi di un'affermazione, dato il suo id.", _ID),
    "info_progetto": (t_info, "Informazioni sul progetto, licenza, avvertenza e data dei dati.", _VUOTO),
}


def _riga(a: dict) -> str:
    fonti = "; ".join(f["url"] for f in a["fonti"]) or "nessun link: vedi la pagina e l'elenco delle fonti del sito"
    pag = a["pagina"] if isinstance(a["pagina"], str) else a["pagina"]["url"]
    return f"[{a['etichetta']} · {a['certezza'] or '—'}] {a['testo']}\nFonte: {fonti}\nPagina: {pag}"


def _testo(nome: str, r: dict) -> str:
    righe = []
    if nome == "cerca_affermazioni":
        righe.append(f"{r['totale']} risultati (mostrati {len(r['risultati'])}).")
        righe += [_riga(a) for a in r["risultati"]]
    elif nome == "get_affermazione":
        righe.append(_riga(r["affermazione"]))
    elif nome == "fonti_di":
        righe.append(_riga(r))
        if r.get("nota"):
            righe.append(r["nota"])
    elif nome == "elenca_temi":
        righe.append("Temi: " + ", ".join(f"{k} ({v})" for k, v in r["temi"].items()))
        righe.append("Etichette: " + ", ".join(f"{k} ({v})" for k, v in r["per_etichetta"].items()))
    else:
        righe.append(f"{r['progetto']} – {r['sito']}\nDati del {r['generato_il']}, "
                     f"{r['conteggi']['affermazioni']} affermazioni. Documentazione: {r['documentazione']}")
    righe.append(f"Etichette: FATTO, STIMA, INTERPRETAZIONE, DA VERIFICARE. Fonte dei dati: {r['fonte_dati']}")
    righe.append(f"{AVVERTENZA} {r['attribuzione']}")
    return "\n\n".join(righe)


def _errore(testo: str) -> dict:
    return {"content": [{"type": "text", "text": f"Errore: {testo} {AVVERTENZA}"}], "isError": True}


def gestisci(msg: dict) -> dict | None:
    metodo, mid = msg.get("method"), msg.get("id")
    if "id" not in msg:  # notifica: nessuna risposta
        return None
    try:
        if msg.get("jsonrpc") != "2.0" or not isinstance(metodo, str):
            return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32600, "message": "richiesta non valida"}}
        if metodo == "initialize":
            richiesto = (msg.get("params") or {}).get("protocolVersion")
            res = {"protocolVersion": richiesto if richiesto in PROTOCOLLI else PROTOCOLLI[0],
                   "capabilities": {"tools": {"listChanged": False}},
                   "serverInfo": {"name": "bilancia-civica", "version": VERSIONE},
                   "instructions": "Dati in sola lettura di Bilancia Civica. " + AVVERTENZA}
        elif metodo == "ping":
            res = {}
        elif metodo == "tools/list":
            res = {"tools": [{"name": n, "description": d, "inputSchema": s, "annotations": _RO}
                             for n, (_, d, s) in TOOLS.items()]}
        elif metodo == "tools/call":
            p = msg.get("params") or {}
            nome, args = p.get("name"), p.get("arguments")
            args = {} if args is None else args
            if nome not in TOOLS:
                return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32602, "message": "strumento sconosciuto"}}
            if not isinstance(args, dict):
                return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32602, "message": "argomenti non validi"}}
            try:
                D.carica()
                r = TOOLS[nome][0](args)
                res = {"content": [{"type": "text", "text": _testo(nome, r)}], "structuredContent": r}
            except (ValueError, DatiNonDisponibili) as e:
                res = _errore(str(e))
            except (OSError, KeyError) as e:
                res = _errore(f"dati non disponibili ({type(e).__name__}).")
        else:
            return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": "metodo non supportato"}}
        return {"jsonrpc": "2.0", "id": mid, "result": res}
    except Exception as e:  # il processo non deve mai interrompersi
        _log(f"errore interno {type(e).__name__}")
        return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32603, "message": "errore interno"}}


def main() -> None:
    for riga in sys.stdin:
        riga = riga.strip()
        if not riga:
            continue
        if len(riga) > 1_000_000:
            out = {"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "richiesta troppo grande"}}
        else:
            try:
                msg = json.loads(riga)
            except json.JSONDecodeError:
                out = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "JSON non valido"}}
            else:
                out = gestisci(msg) if isinstance(msg, dict) else {
                    "jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "richiesta non valida"}}
        if out is not None:
            sys.stdout.write(json.dumps(out, ensure_ascii=False) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
