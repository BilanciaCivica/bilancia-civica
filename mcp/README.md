# Server MCP di Bilancia Civica

Un piccolo programma che permette a un assistente di intelligenza artificiale (per esempio Claude
Desktop o Cursor) di consultare i [dati aperti](https://bilanciacivica.github.io/bilancia-civica/dati.html)
di Bilancia Civica: le affermazioni del sito, con la loro **etichetta** (fatto, stima,
interpretazione, da verificare) e le loro **fonti**.

MCP (*Model Context Protocol*) è un modo standard per collegare un assistente a una fonte di dati.
Il server gira sul tuo computer e l'assistente lo avvia quando serve.

**Contenuti informativi, non consulenza legale.** Per un caso concreto rivolgiti a un avvocato, a un
sindacato, a un patronato o a un'associazione di tutela dei diritti.

## Che cosa fa e che cosa non fa

- **Solo lettura.** Legge tre file pubblici e risponde alle domande. Non scrive, non invia e non
  modifica nulla.
- **Indirizzi fissi.** Scarica solo questi file, in HTTPS:
  - https://bilanciacivica.github.io/bilancia-civica/dati/indice.json
  - https://bilanciacivica.github.io/bilancia-civica/dati/affermazioni.json
  - https://bilanciacivica.github.io/bilancia-civica/dati/fonti.json
- **Cache.** Conserva una copia dei file per 6 ore in `~/.cache/bilancia-civica-mcp`. Se la rete
  non c'è, usa la copia salvata.
- **Funziona anche senza rete** (modalità offline), dopo un primo avvio con la rete.
- **Nessuna telemetria.** Le tue domande restano tra te e il tuo assistente: il server non le
  registra e non le invia a nessuno.
- **Ogni risposta** riporta l'etichetta, la fonte e l'avvertenza «non consulenza legale».

## Che cosa serve

- **Python 3.9 o successivo.** Nient'altro: usa solo la libreria standard, quindi non c'è niente da
  installare con `pip`.
- Un programma che supporta MCP, come Claude Desktop o Cursor.

## Come si scarica

Scarica il repository (pulsante *Code* → *Download ZIP* su GitHub) oppure:

```sh
git clone https://github.com/BilanciaCivica/bilancia-civica.git
```

Il server è un solo file: `mcp/bilancia_civica_mcp.py`. Puoi anche scaricare solo quello:

```sh
curl -O https://raw.githubusercontent.com/BilanciaCivica/bilancia-civica/main/mcp/bilancia_civica_mcp.py
```

Nelle configurazioni qui sotto sostituisci `/percorso/bilancia-civica/mcp/bilancia_civica_mcp.py` con
il percorso vero del file sul tuo computer. Su Windows scrivi il percorso con doppie barre, per esempio
`C:\\Utenti\\nome\\bilancia-civica\\mcp\\bilancia_civica_mcp.py`, e usa `python` o `py` al posto di
`python3`.

## Configurazione

### Claude Desktop

Apri *Impostazioni* → *Sviluppatore* → *Modifica configurazione*. Il file si chiama
`claude_desktop_config.json` (su macOS è in `~/Library/Application Support/Claude/`, su Windows in
`%APPDATA%\Claude\`). Aggiungi:

```json
{
  "mcpServers": {
    "bilancia-civica": {
      "command": "python3",
      "args": ["/percorso/bilancia-civica/mcp/bilancia_civica_mcp.py"]
    }
  }
}
```

Poi chiudi e riapri Claude Desktop.

### Cursor

Crea o modifica il file `~/.cursor/mcp.json` (per tutti i progetti) oppure `.cursor/mcp.json` nella
cartella di un progetto:

```json
{
  "mcpServers": {
    "bilancia-civica": {
      "command": "python3",
      "args": ["/percorso/bilancia-civica/mcp/bilancia_civica_mcp.py"]
    }
  }
}
```

Poi controlla in *Settings* → *MCP* che «bilancia-civica» sia attivo.

### Altri programmi (stdio)

Qualsiasi programma che supporta i server MCP via *stdio* può usarlo con questi dati:

```json
{
  "name": "bilancia-civica",
  "transport": "stdio",
  "command": "python3",
  "args": ["/percorso/bilancia-civica/mcp/bilancia_civica_mcp.py"],
  "env": {}
}
```

### Modalità offline

Per non usare mai la rete aggiungi `"env": {"BILANCIA_OFFLINE": "1"}` alla configurazione, oppure
`"--offline"` dopo il percorso in `args`. Il server usa allora solo la copia in cache: serve quindi
almeno un avvio con la rete. Se preferisci, puoi indicare una cartella con i tre file JSON, per
esempio quella creata da `python3 build.py`, con `"env": {"BILANCIA_DATI_DIR": "/percorso/bilancia-civica/_site/dati"}`.

## Gli strumenti

| Strumento | A che cosa serve |
|---|---|
| `cerca_affermazioni` | Cerca per parole (`testo`), `tema` o `etichetta`; `limite` da 1 a 50, di solito 10. |
| `get_affermazione` | Mostra un'affermazione completa, dato il suo `id`. |
| `elenca_temi` | Elenca i temi e quante affermazioni ci sono per tema e per etichetta. |
| `fonti_di` | Mostra le fonti e gli articoli di legge citati da un'affermazione, dato il suo `id`. |
| `info_progetto` | Dice che cos'è Bilancia Civica, la licenza e la data dei dati. |

Gli argomenti vengono controllati: un'etichetta, un tema o un id non validi producono un messaggio
di errore chiaro, senza effetti.

## Domande di esempio

- «Secondo Bilancia Civica, serve un preavviso per un presidio? Dimmi l'etichetta e la fonte.»
- «Quali affermazioni sul decreto-legge 190/2026 sono ancora da verificare?»
- «Che cosa cambia per lo sciopero? Elenca solo i fatti con la fonte ufficiale.»
- «Mostrami le fonti dell'affermazione presidio-abc0d7d83d.»
- «Di quando sono i dati di Bilancia Civica?»

## Limiti

- I dati valgono alla data indicata (`generato_il`). Le norme cambiano: controlla sempre le fonti
  ufficiali.
- La ricerca è per parole, non per significato: prova parole diverse se non trovi quello che cerchi.
- Il tema di ogni affermazione è assegnato in automatico ed è solo indicativo.
- Alcune affermazioni non hanno un link alla fonte: il server lo segnala.
- L'assistente può riassumere male: controlla sempre l'affermazione sulla pagina del sito, il cui
  link è in ogni risposta.
- Un'affermazione `DA VERIFICARE` non è un fatto e non va presentata come tale.

## Privacy

Il server non raccoglie dati personali, non usa cookie e non manda nulla a Bilancia Civica o ad
altri. L'unico traffico di rete sono le richieste dei tre file pubblici su GitHub Pages, che come ogni
sito vede l'indirizzo IP di chi li scarica. Con la modalità offline non c'è traffico di rete.
Quello che scrivi al tuo assistente è regolato dalle condizioni del servizio che usi.

## Prove

Dalla cartella `mcp`:

```sh
python3 -m unittest discover -s tests -v
```

Le prove usano i dati ridotti in `tests/dati` e non usano la rete. Per provare anche i dati
pubblicati: `BILANCIA_TEST_LIVE=1 python3 -m unittest discover -s tests -v`.

## Licenza

Codice: GNU Affero General Public License v3.0 (AGPL-3.0), vedi [LICENSE](../LICENSE).
Dati: CC BY-SA 4.0, vedi [DATI.md](../DATI.md). Attribuzione: *Bilancia Civica –
https://bilanciacivica.github.io/bilancia-civica/ – CC BY-SA 4.0*.

Segnalazioni: https://github.com/BilanciaCivica/bilancia-civica/issues (sono pubbliche: non inserire
dati personali).
