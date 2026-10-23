# Metodologia di Bilancia Civica

> **Aggiornata al 23/10/2026, ore 20:33 (ora di Roma, CEST).** Versione v0.3. I rimandi a §2 (decreto sicurezza) e §3 (autotrasporto) si riferiscono a [`docs/analisi-dl-190-2026.md`](docs/analisi-dl-190-2026.md).

## 1. Metodologia

### 1.1 Come è organizzato il lavoro

Il lavoro redazionale è diviso in quattro attività, ognuna con compiti e limiti propri.

| Attività | Cosa fa | Cosa non fa |
|---|---|---|
| **Fonti** | Controlla Gazzetta Ufficiale, Normattiva, atti di Camera e Senato (anche dati.camera.it e dati.senato.it), governo.it, ISTAT, UPB, RGS, Commissione di garanzia per lo sciopero, MIT. Registra ogni versione dei documenti ufficiali consultati (impronta SHA-256 e data) e segnala quando un testo ufficiale manca. | Non interpreta. |
| **Diritti** | Cura la Bussola Diritti: artt. 13, 17, 21, 25, 27, 40 Cost., L. 146/1990, art. 18 TULPS, norme penali rilevanti. Distingue la protesta protetta dalle condotte punibili. | Non dà consulenza legale sul caso concreto; non aiuta a eludere la legge né a identificare persone. |
| **Impatto** | Stima l'effetto di una misura su situazioni tipo, **sempre con intervalli** e ipotesi dichiarate; descrive le alternative proposte, con i costi stimati. | Non dà numeri secchi; non chiede dati identificativi e non salva nessuna risposta. |
| **Revisione** | Prima della pubblicazione controlla fonti, etichette e regole di neutralità (§1.2); gestisce correzioni e repliche (§1.10). | Non aggiunge contenuti di merito senza fonte. |

### 1.2 Regole di neutralità

1. **Stessi criteri per tutti gli schieramenti.** Le metriche, le soglie di segnalazione e il formato delle schede sono identici per qualunque governo, partito o coalizione. Una norma viene descritta con lo stesso schema chiunque l'abbia proposta.
2. **Test di simmetria (obbligatorio prima della pubblicazione di una scheda su un tema politico):**
   - *Test di sostituzione:* "Se la stessa misura l'avesse adottata lo schieramento opposto, il testo della scheda cambierebbe?" Se sì, la scheda va riscritta.
   - *Bilanciamento delle voci:* quando si riportano opinioni, si riportano **sia** posizioni critiche **sia** favorevoli realmente espresse e citate. Se una delle due parti non ha espresso posizioni reperibili, si scrive esplicitamente "non trovate posizioni pubbliche di [parte] alla data X" invece di inventarle o di lasciare un vuoto.
   - *Verifica periodica:* ogni mese un campione di schede viene valutato da revisori con orientamenti diversi; i risultati sono pubblicati.
3. **Linguaggio neutro.** Si usano i nomi ufficiali degli atti ("decreto-legge recante disposizioni urgenti in materia di…") e si indicano tra virgolette le formule giornalistiche o politiche ("decreto cortei", "partecipazione violenta"). Niente aggettivi valutativi ("stretta", "bavaglio", "svolta storica") fuori dalle citazioni.
4. **Diritto di replica.** Ogni soggetto citato (persona con ruolo pubblico, partito, ente, associazione) può chiedere una rettifica o aggiungere una replica tramite una segnalazione pubblica (issue sul repository GitHub). La replica viene pubblicata accanto alla scheda, datata, entro 72 ore se pertinente e documentata.
5. **Separazione dei ruoli.** Chi contribuisce codice o schede dichiara eventuali incarichi politici o conflitti di interesse nella segnalazione o nella proposta di modifica (*pull request*) con cui partecipa.


### 1.3 Etichette: FATTO / STIMA / INTERPRETAZIONE / DA VERIFICARE

Ogni affermazione nelle pagine e nelle schede porta **una di quattro etichette**, più un **livello di certezza** (Alta / Media / Bassa) e almeno una fonte.

| Etichetta | Definizione | Requisiti | Esempio |
|---|---|---|---|
| **FATTO** | Affermazione verificabile direttamente su un documento o dato ufficiale, o riportata in modo concorde da più fonti affidabili. | Fonte primaria con collegamento al documento; data della fonte; se la fonte è solo giornalistica, certezza ≤ Media. | "Il decreto-legge 22 ottobre 2026, n. 190 è pubblicato nella GU Serie Generale n. 246 del 22/10/2026." ([GU](https://www.gazzettaufficiale.it/eli/id/2026/10/22/26G00214/SG)). Certezza: Alta. |
| **STIMA** | **Solo valori numerici** calcolati o proiettati. | **Intervallo obbligatorio (min–max)**, ipotesi elencate, dati di partenza con collegamento alla fonte, metodo riproducibile. Un numero senza intervallo non è una STIMA; un giudizio qualitativo non è mai una STIMA. | "Per una famiglia di 3 persone con spesa per energia di X €/mese, l'aumento tendenziale degli energetici a settembre 2026 implica +Y–Z €/mese" (ipotesi: paniere ISTAT, nessun bonus). |
| **INTERPRETAZIONE** | Lettura, valutazione giuridica o politica, giudizio di opportunità, consiglio pratico. | **Sempre attribuita** a un autore o a una fonte identificati (giurista, ente, giudice, partito, governo), con citazione; sulle questioni controverse si riportano le letture contrapposte. Un consiglio pratico neutro, non controverso, si etichetta **"Nota redazionale di Bilancia Civica"**. Nessuna interpretazione anonima. | "Secondo il presidente dell'Unione Camere Penali la norma lede i principi di proporzionalità e determinatezza" ([ANSA](https://www.ansa.it/sito/notizie/cronaca/2026/10/21/penalisti-il-nuovo-decreto-sicurezza-e-inutile-e-lesivo-dei-diritti_aad4edf0-f971-444b-a62c-f8390db3520e.html)), affiancata dalla posizione del governo. |
| **DA VERIFICARE** | Affermazione plausibile o riportata da una fonte, ma **non ancora confermata da fonte primaria**. | Deve indicare **cosa manca** (quale documento o dato) e **come si verificherà** (quale fonte, quando). Non si usa mai come base per un'altra affermazione etichettata FATTO. Certezza: Bassa per definizione. | "Non è chiaro se bengala e fumogeni rientrino tra «razzi» o «fuochi artificiali» dell'art. 420-bis c.p. Manca: dossier dei Servizi studi. Verifica: scheda dell'AC 3159 su camera.it." |

Regole operative:
- Bilancia Civica **non emette interpretazioni proprie** su questioni politiche controverse: riporta quelle altrui, attribuite.
- Le "note redazionali di Bilancia Civica" sono ammesse solo per indicazioni pratiche neutre (per esempio "conserva la ricevuta del preavviso"), mai per giudizi su norme, persone o schieramenti.
- Quando una fonte primaria conferma un punto DA VERIFICARE, l'etichetta passa a FATTO e la modifica va nel registro delle modifiche della scheda.

### 1.4 Gerarchia delle fonti

In caso di conflitto prevale la fonte di livello più alto; la discrepanza viene **sempre segnalata** nella scheda.

1. **Fonti primarie ufficiali:** Gazzetta Ufficiale, Normattiva, Costituzione, atti parlamentari (camera.it, senato.it, dati.camera.it, dati.senato.it), comunicati del CdM (governo.it), decreti e comunicati ministeriali (per esempio mit.gov.it, mef.gov.it), sentenze della Corte costituzionale.
2. **Organi tecnici e di garanzia:** UPB (Ufficio parlamentare di bilancio), RGS (Ragioneria generale dello Stato, relazioni tecniche), ISTAT, Corte costituzionale, Corte dei conti, Banca d'Italia, ANAC, Commissione di garanzia sciopero, Servizi studi di Camera e Senato (dossier).
3. **Agenzie di stampa:** ANSA, AGI, Adnkronos, LaPresse, DIRE.
4. **Testate giornalistiche e riviste specializzate** (incluse riviste giuridiche come Sistema Penale).
5. **Fonti di parte** (comunicati di partiti, sindacati, associazioni, imprese): ammesse solo come fonte della **loro posizione**, mai come fonte di un fatto non riscontrato altrove.

### 1.5 Regole su date e versioni

- Ogni scheda riporta: **data/ora di aggiornamento (ora di Roma)**, **versione** (numerazione progressiva: 0.1, 0.2…), **stato dell'atto** (approvato dal CdM / pubblicato in GU / in vigore / in conversione / convertito / decaduto).
- Ogni documento ufficiale consultato viene registrato con URL, data di accesso, impronta SHA-256; le modifiche producono una nuova versione e un confronto con la precedente.
- Per i decreti-legge si traccia: data del CdM → data di emanazione → GU (numero, data) → entrata in vigore → scadenza dei 60 giorni (art. 77 Cost.) → esito.
- Data e ora in formato ISO 8601 con fuso esplicito; nei testi pubblicati si usa l'ora di Roma, indicata come tale.

### 1.6 Cosa fare se manca il testo ufficiale

Caso tipico: decreto approvato dal CdM ma non ancora pubblicato in GU (situazione del decreto sicurezza tra il 20 e il 22/10/2026, superata con la pubblicazione del D.L. 190/2026 nella GU n. 246 del 22/10/2026).

1. La scheda viene marcata **"⚠️ TESTO UFFICIALE NON DISPONIBILE"** in testa.
2. Si usa come base il **comunicato del CdM** (livello 1) e si dichiara che non è un testo normativo.
3. Le bozze circolate (per esempio pubblicate da siti terzi) si citano solo come "bozza non ufficiale", certezza massima: Bassa–Media.
4. Le norme **non vengono descritte come vigenti**. Formula obbligatoria: "secondo il testo approvato dal CdM / secondo la bozza, se confermato in GU…".
5. Le discrepanze tra comunicato, bozza e agenzie vengono elencate in una tabella dedicata.
6. Appena il testo viene pubblicato, la scheda viene rigenerata e confrontata con la versione precedente, e la pagina «Stato degli atti seguiti» viene aggiornata.

### 1.7 Limiti espliciti

- Lo strumento **non è un avvocato** né un consulente fiscale; non valuta casi individuali.
- Le stime d'impatto dipendono dalle ipotesi; sono intervalli indicativi, non previsioni certe.
- Le fonti giornalistiche possono contenere errori; Bilancia Civica può riportarli se non riscontrabili altrove (in tal caso la certezza è dichiarata Bassa/Media).
- La copertura iniziale è limitata (atti nazionali; non quelli regionali o comunali nella prima versione).
- Anche con questi controlli possono restare errori: ogni pagina contiene i link per la verifica e il modo per segnalarli.
- Bilancia Civica non prevede esiti giudiziari né decisioni della Corte costituzionale.

### 1.8 Privacy e GDPR

- **Nessuna profilazione degli utenti.** Bilancia Civica non raccoglie opinioni, appartenenze o partecipazione a manifestazioni.
- **Il simulatore non salva nessun dato**, nemmeno in forma anonima e nemmeno con il consenso di chi lo usa. Le risposte (fasce di reddito, composizione familiare e simili) servono solo per il calcolo mostrato a schermo e non vengono registrate. Non esistono profili utente.
- Il sito pubblico non usa cookie, non traccia i visitatori, non carica font o script esterni e non raccoglie dati.
- Il sito è ospitato su GitHub Pages. Secondo la [documentazione di GitHub](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages), in inglese, GitHub registra l'indirizzo IP dei visitatori per motivi di sicurezza; Bilancia Civica non ha accesso a quei dati.
- Si trattano dati personali solo di **persone con ruolo pubblico** e solo in relazione al loro ruolo (voti, incarichi, dichiarazioni pubbliche), con base giuridica nel legittimo interesse/finalità giornalistiche-informative (art. 85 GDPR) e nel rispetto del Codice privacy.
- **Divieti assoluti:** identificare manifestanti, agenti o minori da foto/video; raccogliere dati di partecipanti a cortei; fornire indicazioni per sottrarsi all'identificazione o commettere reati.

### 1.9 Niente consulenza legale

Ogni pagina della Bussola Diritti riporta: *"Informazione generale, non consulenza legale. Per un caso concreto: avvocato, sindacato, associazioni di tutela dei diritti."* Le pagine non danno indicazioni sul caso individuale (per esempio "cosa devo dire alla polizia nel mio caso"): offrono informazione generale sui diritti (per esempio il diritto a un difensore) e indicano a chi rivolgersi.

### 1.10 Registro correzioni

- File pubblico `CORREZIONI.md` e pagina web: data, scheda, testo errato, testo corretto, chi ha segnalato (se consente), causa.
- Obiettivo: presa in carico entro 24 ore, correzione entro 48 ore per errori di fatto.
- Le correzioni sostanziali vengono segnalate in evidenza nella pagina interessata, oltre che nel registro.

### 1.11 Dati di terzi

Quando una scheda usa dati raccolti o elaborati da altri progetti:

1. si citano il progetto, il dataset e la data della consultazione, e quando possibile si risale alla fonte primaria;
2. se la licenza non è dichiarata, si cita e si rimanda al dato, ma **non si ridistribuiscono righe grezze** (niente copie integrali, file CSV o tabelle copiate);
3. ciò che emerge è un **segnale da verificare** sulla fonte primaria, mai un'accusa o la prova di un'irregolarità;
4. **niente nomi di persone fisiche**, anche se pubblici alla fonte; enti, amministrazioni e società si citano per ruolo e importo;
5. un dato di terzi riscontrato sulla fonte primaria può essere FATTO; finché non è riscontrato è DA VERIFICARE.

---
