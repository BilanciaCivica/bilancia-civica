---
titolo: Dati aperti (JSON)
descrizione: Le affermazioni di Bilancia Civica in formato JSON, con etichetta, certezza, articoli di legge citati e fonti. Licenza CC BY-SA 4.0.
---
# Dati aperti (JSON)

::: inbreve
**In breve**

- Le affermazioni con etichetta del sito sono disponibili anche come **file JSON**, un formato che i programmi leggono facilmente.
- Per ogni affermazione ci sono il testo, l'etichetta, la certezza, gli articoli di legge citati, i link alle fonti e il punto della pagina in cui si trova.
- I file nascono dagli stessi testi del sito: quando cambia una pagina, cambiano anche i dati.
:::

## I file

| File | Che cosa contiene |
|---|---|
| [indice.json](dati/indice.json) | Descrizione dei dati: versione, data, licenza, conteggi per etichetta e per tema, elenco dei file |
| [affermazioni.json](dati/affermazioni.json) | Le affermazioni, una per voce |
| [fonti.json](dati/fonti.json) | Le fonti citate, senza doppioni, con le affermazioni che le usano |
| [schema-affermazioni.json](dati/schema-affermazioni.json) | Lo schema che descrive i campi (formato JSON Schema) |

## Che cosa c'è in ogni affermazione

- **Codice (id):** resta uguale finché non cambiano il testo o l'etichetta dell'affermazione.
- **Testo ed etichetta:** fatto, stima, interpretazione o da verificare, con la certezza (Alta, Media o Bassa) quando è indicata.
- **Riferimenti normativi:** gli articoli e gli atti citati, per esempio l'art. 17 della Costituzione.
- **Fonti:** titolo e link. Il campo «ufficiale» indica i siti istituzionali, come Gazzetta Ufficiale, Normattiva, Camera e Governo.
- **Pagina:** il link al punto esatto del sito in cui si trova l'affermazione.
- **Data di aggiornamento** dei testi.

La descrizione completa dei campi e delle regole di lettura è in [DATI.md](DATI.md).

## Usarli con un assistente di intelligenza artificiale

Chi usa un assistente come Claude Desktop o Cursor può collegarlo a questi dati con un piccolo programma (un «server MCP») che gira sul proprio computer. Legge solo i file pubblici di questa pagina, non registra le domande e in ogni risposta riporta etichetta, fonte e avvertenza. Istruzioni nel [repository]({{REPO}}/tree/main/mcp).

## Come riutilizzarli

Puoi copiare, modificare e ridistribuire i dati, anche per fini commerciali, con la licenza **CC BY-SA 4.0**: cita Bilancia Civica con il link al sito, indica se hai fatto modifiche e usa la stessa licenza. Attribuzione suggerita: *Bilancia Civica – https://bilanciacivica.github.io/bilancia-civica/ – CC BY-SA 4.0*.

La licenza non si applica ai testi degli atti ufficiali (art. 5 L. 633/1941) né alle citazioni di terzi, che restano dei rispettivi autori.

Quando riprendi un'affermazione, riporta anche la sua **etichetta** e la **fonte**: un'affermazione «da verificare» non va presentata come un fatto.

## Avvertenze

- **Contenuti informativi, non consulenza legale.** Per un caso concreto è opportuno rivolgersi a un avvocato, a un sindacato, a un patronato o a un'associazione di tutela dei diritti.
- I dati valgono alla data indicata nei file. Le norme possono cambiare: controlla sempre le fonti ufficiali.
- Il tema di ogni affermazione (presidi, cortei, sciopero e così via) è assegnato in automatico ed è solo indicativo.
- Alcune affermazioni non hanno un link alla fonte nella stessa frase: nei dati sono segnalate. In quel caso cerca la fonte nella stessa sezione della pagina o nell'elenco delle [fonti](fonti.html).
- I file non contengono dati sui visitatori: il sito non ne raccoglie.

## Segnalare un errore

Se trovi un errore, apri una [segnalazione su GitHub]({{REPO}}/issues) e indica il codice (id) dell'affermazione. Le segnalazioni sono pubbliche: non inserire dati personali, tuoi o di altre persone. Le correzioni confermate sono registrate nel [registro delle correzioni](CORREZIONI.md).
