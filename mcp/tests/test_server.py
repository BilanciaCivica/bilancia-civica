# SPDX-License-Identifier: AGPL-3.0-only
"""Test del server MCP. Uso, dalla cartella ``mcp``: python3 -m unittest discover -s tests -v

Senza rete: usano i dati ridotti in ``tests/dati``. Il test sui dati pubblicati parte solo con
BILANCIA_TEST_LIVE=1.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

QUI = Path(__file__).resolve().parent
SERVER = QUI.parent / "bilancia_civica_mcp.py"
DATI = QUI / "dati"
sys.path.insert(0, str(SERVER.parent))
import bilancia_civica_mcp as m  # noqa: E402


def chiama(nome, args=None, mid=1):
    return m.gestisci({"jsonrpc": "2.0", "id": mid, "method": "tools/call",
                       "params": {"name": nome, "arguments": args if args is not None else {}}})


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.env = mock.patch.dict(os.environ, {"BILANCIA_DATI_DIR": str(DATI), "XDG_CACHE_HOME": self.tmp,
                                                "BILANCIA_OFFLINE": ""})
        self.env.start()
        m.D = m.Dati()
        # nessun test deve usare la rete
        self.rete = mock.patch("urllib.request.urlopen", side_effect=AssertionError("rete non ammessa"))
        self.rete.start()

    def tearDown(self):
        self.rete.stop()
        self.env.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def ok(self, nome, args=None):
        r = chiama(nome, args)["result"]
        self.assertFalse(r.get("isError"), r)
        testo, sc = r["content"][0]["text"], r["structuredContent"]
        # ogni risposta: avvertenza, etichette e fonte dei dati
        self.assertIn("non consulenza legale", testo)
        self.assertIn("DA VERIFICARE", testo)
        self.assertIn("Fonte", testo)
        self.assertEqual(sc["avvertenza"], m.AVVERTENZA)
        self.assertTrue(sc["fonte_dati"].startswith("https://bilanciacivica.github.io/"))
        return r

    def errore(self, nome, args):
        r = chiama(nome, args)["result"]
        self.assertTrue(r["isError"], r)
        self.assertIn("non consulenza legale", r["content"][0]["text"])
        return r["content"][0]["text"]


class Protocollo(Base):
    def test_initialize(self):
        for v in m.PROTOCOLLI:
            r = m.gestisci({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": v}})
            self.assertEqual(r["result"]["protocolVersion"], v)
        r = m.gestisci({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "1999-01-01"}})
        self.assertEqual(r["result"]["protocolVersion"], m.PROTOCOLLI[0])
        self.assertEqual(r["result"]["serverInfo"]["name"], "bilancia-civica")

    def test_tools_list(self):
        t = m.gestisci({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})["result"]["tools"]
        self.assertEqual({x["name"] for x in t},
                         {"cerca_affermazioni", "get_affermazione", "elenca_temi", "fonti_di", "info_progetto"})
        for x in t:
            self.assertTrue(x["annotations"]["readOnlyHint"])
            self.assertFalse(x["inputSchema"]["additionalProperties"])

    def test_notifica_ping_errori(self):
        self.assertIsNone(m.gestisci({"jsonrpc": "2.0", "method": "notifications/initialized"}))
        self.assertEqual(m.gestisci({"jsonrpc": "2.0", "id": 3, "method": "ping"})["result"], {})
        self.assertEqual(m.gestisci({"jsonrpc": "2.0", "id": 4, "method": "resources/list"})["error"]["code"], -32601)
        self.assertEqual(m.gestisci({"id": 5, "method": "ping"})["error"]["code"], -32600)
        self.assertEqual(chiama("cancella_tutto")["error"]["code"], -32602)
        r = m.gestisci({"jsonrpc": "2.0", "id": 6, "method": "tools/call",
                        "params": {"name": "elenca_temi", "arguments": [1]}})
        self.assertEqual(r["error"]["code"], -32602)


class Strumenti(Base):
    def test_cerca(self):
        sc = self.ok("cerca_affermazioni", {"testo": "decreto legge"})["structuredContent"]
        self.assertGreaterEqual(sc["totale"], 1)
        for a in sc["risultati"]:
            self.assertIn(a["etichetta"], m.ETICHETTE)
            self.assertIn("fonti", a)
            self.assertIn("pagina", a)

    def test_cerca_filtri_e_accenti(self):
        sc = self.ok("cerca_affermazioni", {"etichetta": "DA VERIFICARE"})["structuredContent"]
        self.assertEqual(sc["totale"], 1)
        self.assertTrue(all(a["etichetta"] == "DA VERIFICARE" for a in sc["risultati"]))
        sc = self.ok("cerca_affermazioni", {"tema": "presidi", "limite": 2})["structuredContent"]
        self.assertEqual((sc["totale"], len(sc["risultati"])), (4, 2))
        a = self.ok("cerca_affermazioni", {"testo": "E IL DECRETO"})["structuredContent"]  # "È" senza accento
        self.assertIn("home-b94d95c585", [x["id"] for x in a["risultati"]])

    def test_get_e_fonti(self):
        r = self.ok("get_affermazione", {"id": "home-b94d95c585"})
        self.assertEqual(r["structuredContent"]["affermazione"]["etichetta"], "FATTO")
        self.assertIn("[FATTO · Alta]", r["content"][0]["text"])
        r = self.ok("fonti_di", {"id": "home-b94d95c585"})
        self.assertTrue(r["structuredContent"]["fonti"])
        self.assertIn("gazzettaufficiale.it", r["content"][0]["text"])
        r = self.ok("fonti_di", {"id": "presidio-cf60ee74d2"})
        self.assertEqual(r["structuredContent"]["etichetta"], "DA VERIFICARE")
        self.assertIn("nota", r["structuredContent"])

    def test_temi_e_info(self):
        sc = self.ok("elenca_temi")["structuredContent"]
        self.assertEqual(sc["temi"], {"decreto-sicurezza": 1, "presidi": 4})
        sc = self.ok("info_progetto")["structuredContent"]
        self.assertEqual(sc["conteggi"]["affermazioni"], 5)
        self.assertIn("CC BY-SA", sc["licenza"]["testi"])

    def test_validazione(self):
        casi = [
            ("cerca_affermazioni", {"etichetta": "OPINIONE"}, "etichetta"),
            ("cerca_affermazioni", {"tema": "inesistente"}, "tema"),
            ("cerca_affermazioni", {"limite": 0}, "limite"),
            ("cerca_affermazioni", {"limite": 51}, "limite"),
            ("cerca_affermazioni", {"limite": True}, "limite"),
            ("cerca_affermazioni", {"limite": "5"}, "limite"),
            ("cerca_affermazioni", {"testo": "x" * 201}, "testo"),
            ("cerca_affermazioni", {"testo": 5}, "testo"),
            ("cerca_affermazioni", {"url": "https://esempio.it"}, "non previsti"),
            ("get_affermazione", {}, "obbligatorio"),
            ("get_affermazione", {"id": "../../etc/passwd"}, "non valido"),
            ("get_affermazione", {"id": "non-esiste"}, "non trovato"),
            ("fonti_di", {"id": "A" * 81}, "non valido"),
            ("elenca_temi", {"x": 1}, "non previsti"),
            ("info_progetto", {"x": 1}, "non previsti"),
        ]
        for nome, args, atteso in casi:
            with self.subTest(nome=nome, args=args):
                self.assertIn(atteso, self.errore(nome, args))


class CacheOffline(Base):
    def setUp(self):
        super().setUp()
        os.environ.pop("BILANCIA_DATI_DIR")
        os.environ["BILANCIA_OFFLINE"] = "1"

    def test_offline_senza_cache(self):
        self.assertIn("offline", self.errore("info_progetto", {}))

    def test_offline_con_cache(self):
        cache = Path(self.tmp, "bilancia-civica-mcp")
        cache.mkdir()
        for n in m.FILE:
            shutil.copy(DATI / n, cache / n)
        sc = self.ok("info_progetto")["structuredContent"]
        self.assertTrue(sc["dati_da_cache"])

    def test_rete_assente_usa_cache_scaduta(self):
        os.environ["BILANCIA_OFFLINE"] = ""
        cache = Path(self.tmp, "bilancia-civica-mcp")
        cache.mkdir()
        for n in m.FILE:
            shutil.copy(DATI / n, cache / n)
            os.utime(cache / n, (0, 0))  # cache scaduta
        self.rete.stop()
        with mock.patch("urllib.request.urlopen", side_effect=OSError("rete assente")) as u:
            sc = self.ok("elenca_temi")["structuredContent"]
        self.rete.start()
        self.assertTrue(sc["dati_da_cache"])
        self.assertEqual(u.call_args_list[0].args[0].full_url, m.BASE + "indice.json")


class Stdio(unittest.TestCase):
    def test_sessione(self):
        msgs = [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
            {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
             "params": {"name": "cerca_affermazioni", "arguments": {"testo": "decreto"}}},
        ]
        righe = "\n".join(json.dumps(x) for x in msgs) + "\nnon json\n[1]\n"
        with tempfile.TemporaryDirectory() as tmp:
            env = dict(os.environ, BILANCIA_DATI_DIR=str(DATI), XDG_CACHE_HOME=tmp)
            p = subprocess.run([sys.executable, str(SERVER)], input=righe, capture_output=True,
                               text=True, env=env, timeout=60)
        out = [json.loads(x) for x in p.stdout.splitlines()]
        self.assertEqual([x["id"] for x in out], [1, 2, 3, None, None])
        self.assertEqual(out[3]["error"]["code"], -32700)
        self.assertEqual(out[4]["error"]["code"], -32600)
        self.assertEqual(p.stderr, "")


@unittest.skipUnless(os.environ.get("BILANCIA_TEST_LIVE") == "1", "imposta BILANCIA_TEST_LIVE=1")
class DatiPubblicati(unittest.TestCase):
    def test_live(self):
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.dict(os.environ, {"XDG_CACHE_HOME": tmp, "BILANCIA_OFFLINE": ""}):
            os.environ.pop("BILANCIA_DATI_DIR", None)
            m.D = m.Dati()
            r = chiama("info_progetto")["result"]
            self.assertFalse(r.get("isError"), r)
            sc = r["structuredContent"]
            self.assertFalse(sc["dati_da_cache"])
            self.assertEqual(sc["conteggi"]["affermazioni"], len(m.D.affermazioni))
            r = chiama("cerca_affermazioni", {"testo": "preavviso", "limite": 3})["result"]
            self.assertFalse(r.get("isError"), r)
            self.assertGreater(r["structuredContent"]["totale"], 0)
            for n in m.FILE:  # la cache è stata scritta
                self.assertTrue(Path(tmp, "bilancia-civica-mcp", n).exists())


if __name__ == "__main__":
    unittest.main()
