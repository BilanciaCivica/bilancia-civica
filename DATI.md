# Dati aperti di Bilancia Civica

Le affermazioni con etichetta del sito sono pubblicate anche in formato **JSON**, perché si possano
cercare, controllare e riutilizzare con un programma. Pagina per chi legge il sito:
https://bilanciacivica.github.io/bilancia-civica/dati.html

> **Contenuti informativi, non consulenza legale.** Le fonti ufficiali restano il riferimento; per un
> caso concreto è opportuno rivolgersi a un avvocato, a un sindacato, a un patronato o a
> un'associazione di tutela dei diritti.

## I file

Tutti i file sono in `https://bilanciacivica.github.io/bilancia-civica/dati/`, codificati in UTF-8.

| File | Che cosa contiene |
| --- | --- |
| [`indice.json`](https://bilanciacivica.github.io/bilancia-civica/dati/indice.json) | Versione dello schema, data, licenza, avvertenza, significato delle etichette, conteggi (per etichetta, tema e pagina), controlli dell'estrazione ed elenco dei file |
| [`affermazioni.json`](https://bilanciacivica.github.io/bilancia-civica/dati/affermazioni.json) | Le affermazioni, nell'ordine in cui compaiono sul sito |
| [`fonti.json`](https://bilanciacivica.github.io/bilancia-civica/dati/fonti.json) | Le fonti collegate, senza doppioni, ognuna con gli id delle affermazioni che la usano |
| [`schema-affermazioni.json`](https://bilanciacivica.github.io/bilancia-civica/dati/schema-affermazioni.json) | Lo schema di `affermazioni.json` (JSON Schema, versione 2020-12) |

I file vengono generati da `build.py` insieme alle pagine HTML (`python3 build.py` li scrive in
`_site/dati/`). Lo schema si trova nel repository in `dati/schema-affermazioni.json`.

## I campi di un'affermazione

| Campo | Significato |
| --- | --- |
| `id` | Codice stabile: nome della pagina + 10 caratteri esadecimali (vedi sotto) |
| `testo` | Il testo come appare sul sito, senza l'etichetta |
| `etichetta` | `FATTO`, `STIMA`, `INTERPRETAZIONE` o `DA VERIFICARE` |
| `certezza` | `Alta`, `Media`, `Bassa`, oppure `null` se la pagina non la indica |
| `nota_etichetta` | Precisazione scritta accanto all'etichetta, se c'è; altrimenti `null` |
| `etichetta_ereditata` | `true` se l'etichetta è scritta una sola volta per un intero elenco o una tabella e vale per ogni voce |
| `contesto` | Testo vicino che aiuta a capire l'affermazione: intestazione dell'elenco, prima cella della riga, frase che segue senza etichetta propria. Non è un'affermazione etichettata |
| `tema` | `presidi`, `cortei`, `sciopero`, `decreto-sicurezza`, `autotrasporto`, `legge-di-bilancio`, `bollo-auto` o `generale`. È assegnato in automatico (pagina, poi titolo della sezione, poi parole del testo): è solo indicativo |
| `pagina` | `url` con l'ancora al punto esatto (`…#af-<id>`), `titolo` della pagina e `sezione` (ultimo titolo di secondo o terzo livello) |
| `riferimenti_normativi` | Articoli e atti citati nel testo: `citazione` (come è scritta), `atto` (per esempio `Costituzione`, `Codice penale`, `D.L. 190/2026`) e `articolo`. `atto` è `null` quando il testo cita un articolo senza dire di quale atto; `articolo` è `null` quando è citato l'atto intero |
| `fonti` | Fonti con `titolo`, `url`, `ufficiale` e `origine` (vedi sotto) |
| `senza_fonte_collegata` | `true` se né la frase né gli atti citati portano a un link. In quel caso la fonte va cercata nella stessa sezione della pagina o nell'elenco delle fonti del sito |
| `data_aggiornamento` | Data e ora (fuso di Roma) a cui sono aggiornati i testi |

### Fonti

- `origine: "collegamento nel testo"`: il link compare nella frase o nell'etichetta sul sito, oppure
  nell'intestazione o nella frase di introduzione dell'elenco o della tabella che contiene la voce.
- `origine: "riferimento normativo citato"`: il link non compare nella frase, ma la frase cita un atto
  (per esempio «art. 17 Cost.») e il link porta al testo ufficiale di quell'atto su Normattiva,
  Gazzetta Ufficiale o sito della Corte costituzionale. Se la frase cita solo l'articolo («art. 7») e
  l'atto è chiaro dal contesto della pagina, l'atto è indicato da una direttiva `atti` (vedi sotto).
- `ufficiale: true` indica i siti istituzionali (Gazzetta Ufficiale, Normattiva, Parlamento, Governo,
  ministeri, Corte costituzionale, altre amministrazioni pubbliche). Gli articoli di giornale e i siti
  di associazioni hanno `ufficiale: false`.

## Codici (id) stabili

L'`id` è formato dal nome della pagina e dai primi 10 caratteri dell'impronta SHA-256 di
`ETICHETTA|testo normalizzato` (spazi uniformati, maiuscole e minuscole ignorate). Se due affermazioni
della stessa pagina coincidono, la seconda riceve il suffisso `-2`.

- Lo stesso `id` resta valido finché non cambiano il testo o l'etichetta.
- Se una correzione cambia il testo o l'etichetta, cambia anche l'`id`: è voluto, perché
  l'affermazione non è più la stessa. Le correzioni sono registrate in [CORREZIONI.md](CORREZIONI.md).
- L'`id` è anche l'ancora nella pagina: `https://bilanciacivica.github.io/bilancia-civica/<pagina>.html#af-<id>`.

## Come vengono letti i testi

Le affermazioni non sono copiate a mano: `dati.py` le legge dall'HTML che `build.py` genera dagli
stessi file Markdown delle pagine. Le regole:

1. Un'**etichetta** (`[FATTO · Alta]`, `[DA VERIFICARE]`, oppure `**FATTO, certezza Alta**`) appartiene
   al testo che la segue, se si trova a inizio frase o dopo un titolo breve (per esempio
   `**Identificazione** [FATTO · Alta]: …`); altrimenti al testo che la precede.
2. `[DA VERIFICARE]` vale per il testo che segue; il testo prima diventa `contesto`.
3. Un'etichetta scritta da sola, o in un'intestazione breve o che finisce con «:», sopra un elenco o
   una tabella vale per ogni voce (`etichetta_ereditata: true`).
4. Le voci segnate come **[Nota redazionale di Bilancia Civica]** non sono affermazioni etichettate e
   non vengono incluse.
5. Le legende che usano le etichette solo come esempio sono escluse.

Dove la struttura della pagina non basta, il Markdown contiene una **direttiva** in un commento,
invisibile sul sito e rimossa dall'HTML pubblicato:

| Direttiva | Effetto |
| --- | --- |
| `<!-- dati: esempio -->` | Il blocco seguente usa le etichette solo come esempio: è escluso |
| `<!-- dati: intestazione -->` | L'etichetta del blocco seguente vale per tutti i blocchi successivi, fino al prossimo titolo o separatore |
| `<!-- dati: intestazione-precedente -->` | L'etichetta del blocco seguente vale per l'elenco o la tabella che lo precede |
| `<!-- dati: atti D.L. 190/2026 -->` | Nel blocco seguente gli articoli citati senza atto sono di quell'atto |
| `<!-- dati: atti 419, 635.1 = Codice penale; 7 = D.L. 190/2026 -->` | Come sopra, articolo per articolo |

Si possono scrivere più direttive di seguito: valgono tutte per il blocco seguente. Se il blocco è una
frase di introduzione senza etichetta che finisce con «:», la direttiva `atti` vale per l'elenco che
segue. La direttiva `atti` assegna l'atto solo agli articoli che ne sono privi e non cambia il testo;
accetta solo atti con un testo ufficiale collegato.

La generazione si ferma con un errore se trova una direttiva sconosciuta, un'etichetta non valida,
un'etichetta isolata senza testo, oppure una direttiva `atti` con un atto sconosciuto o con un articolo
che il blocco non cita. In `indice.json`, `controllo_estrazione` riporta per ogni pagina il
numero di etichette trovate nell'HTML, quante sono esempi, quante sono intestazioni e quante
affermazioni sono state estratte: le etichette nell'HTML sono sempre uguali alla somma di affermazioni
con etichetta propria, intestazioni ed esempi.

## Usarli da un assistente (server MCP)

Nella cartella [`mcp/`](mcp/) c'è un server MCP (*Model Context Protocol*) che permette a un
assistente di intelligenza artificiale, come Claude Desktop o Cursor, di cercare le affermazioni e
leggerne etichetta e fonti. È un solo file Python con la sola libreria standard, gira sul computer di
chi lo usa, è in sola lettura, scarica solo `indice.json`, `affermazioni.json` e `fonti.json` dagli
indirizzi qui sopra, tiene una copia in cache, funziona anche offline e non registra né invia le
domande. Ogni risposta riporta etichetta, fonte e avvertenza. Istruzioni e configurazione in
[mcp/README.md](mcp/README.md).

## Stabilità e versioni

- `versione_schema` segue la numerazione *x.y.z*: cambia *x* se un campo viene tolto o cambia
  significato, *y* se ne viene aggiunto uno, *z* per correzioni che non toccano i campi.
- Storico: **1.0.1** (24/10/2026), direttiva `<!-- dati: atti … -->` per collegare gli articoli
  all'atto; **1.0.2** (29/10/2026), nuovo valore `bollo-auto` del campo `tema`. I campi non cambiano.
- `generato_il` coincide con la data di aggiornamento dei testi: due generazioni dagli stessi testi
  producono file identici, byte per byte.
- L'ordine è fisso: le affermazioni seguono l'ordine delle pagine e del testo, le fonti l'ordine
  alfabetico dell'indirizzo.

## Licenza e attribuzione

I dati derivano dai testi originali di Bilancia Civica e sono rilasciati con licenza
**Creative Commons Attribuzione – Condividi allo stesso modo 4.0** (CC BY-SA 4.0), vedi
[LICENSE-TESTI](LICENSE-TESTI) e la [sintesi in italiano](https://creativecommons.org/licenses/by-sa/4.0/deed.it).
Puoi copiarli, modificarli e ridistribuirli, anche per fini commerciali, se citi la fonte, indichi le
modifiche e usi la stessa licenza.

Attribuzione suggerita: *Bilancia Civica – https://bilanciacivica.github.io/bilancia-civica/ – CC BY-SA 4.0*.

Sono **esclusi** dalla licenza i testi degli atti ufficiali, non protetti dal diritto d'autore
(art. 5 L. 633/1941), e le citazioni di terzi, che restano dei rispettivi autori (art. 70 L. 633/1941).
Il codice (`build.py`, `dati.py`, `mcp/`) è in licenza GNU AGPL-3.0, vedi [LICENSE](LICENSE).

Chi riusa un'affermazione dovrebbe riportarne anche l'etichetta e la fonte: un'affermazione
`DA VERIFICARE` non va presentata come un fatto.

## Dati personali

I file non contengono dati sui visitatori: il sito non ne raccoglie. Le persone pubbliche compaiono
solo per dichiarazioni o atti pubblici, come sul sito; le loro opinioni sono attribuite e portano
l'etichetta `INTERPRETAZIONE`. Non ci sono dati personali di privati.

## Segnalare un errore

Apri una segnalazione su GitHub (https://github.com/BilanciaCivica/bilancia-civica/issues) e indica
l'`id` dell'affermazione, che cosa non va e, se puoi, la fonte corretta. Le segnalazioni sono
pubbliche: non inserire dati personali, tuoi o di altre persone. Le correzioni confermate sono
registrate in [CORREZIONI.md](CORREZIONI.md).
