# Contribuire a Bilancia Civica

> **Aggiornato al 23/10/2026, ore 23:13 (ora di Roma, CEST).**
>
> Repository: [https://github.com/BilanciaCivica/bilancia-civica](https://github.com/BilanciaCivica/bilancia-civica) · Sito: [https://bilanciacivica.github.io/bilancia-civica/](https://bilanciacivica.github.io/bilancia-civica/)

Grazie per voler contribuire. Bilancia Civica è **imparziale e apartitica**: ogni contributo deve rispettare il [metodo](METODOLOGIA.md).

## Regole sui contenuti

1. **Niente numeri inventati.** Se un dato manca si scrive «non disponibile»; se è riportato ma non confermato, «DA VERIFICARE».
2. **Ogni affermazione indica la sua fonte, con il collegamento al documento**, preferibilmente primaria (Gazzetta Ufficiale, Normattiva, Camera, Senato, ministeri, ISTAT, UPB, Corte costituzionale).
3. **Quattro etichette**, più la certezza (Alta / Media / Bassa):
   - **FATTO**: verificabile sulla fonte indicata.
   - **STIMA**: solo per numeri, sempre come intervallo con ipotesi e metodo.
   - **INTERPRETAZIONE**: sempre attribuita a chi l'ha espressa (persona, ente, testata). Un consiglio pratico neutro si contrassegna come «Nota redazionale di Bilancia Civica».
   - **DA VERIFICARE**: affermazione plausibile o riportata da una fonte ma non ancora confermata da fonte primaria; deve indicare **cosa manca** e **come si verificherà**.
4. **Simmetria.** Posizioni di maggioranza e opposizione con gli stessi criteri: citazione testuale, fonte, data.
5. **Date e orari** in ora di Roma; ogni documento riporta in testa data e ora dell'ultimo aggiornamento.
6. **Niente consulenza legale** e niente aiuto a identificare manifestanti o agenti.
7. **Nessun dato degli utenti.** Il sito e il simulatore non raccolgono né salvano dati, nemmeno in forma anonima: non proporre moduli, registri o profili.

## Dati di terzi

Se usi dati raccolti o elaborati da altri progetti:

- cita il progetto, il dataset e la data della consultazione, e risali alla fonte primaria quando possibile;
- se la licenza non è dichiarata, **non ridistribuire righe grezze** (niente copie integrali o file CSV nel repository);
- presenta i risultati come **segnali da verificare**, **mai come accuse**;
- **non pubblicare nomi di persone fisiche**.

Dettagli in [METODOLOGIA, §1.11](METODOLOGIA.md#111-dati-di-terzi).

## Testi e sito

- I testi delle pagine stanno in `contenuti/*.md` (Markdown semplice). I documenti lunghi sono `METODOLOGIA.md`, `CONTRIBUTING.md` e `docs/*.md`, e diventano anch'essi pagine del sito.
- Dopo ogni modifica rigenera e controlla il sito in locale:
  ```bash
  python3 build.py                        # scrive _site/ (escluso da git)
  python3 -m http.server -d _site 8000    # apri http://localhost:8000
  ```
- Il generatore `build.py` usa solo la libreria standard di Python. Non aggiungere dipendenze, script, font o servizi esterni, cookie o strumenti di tracciamento.
- Ogni pagina che parla di un atto riporta la data di aggiornamento; quando cambia lo stato di un atto aggiorna anche `contenuti/stato.md`.
- **Mai** inserire nel repository segreti, credenziali o dati personali. Non si modificano le versioni archiviate: una nuova versione di un documento va in un nuovo file, con il registro delle modifiche.

## Correzioni

Gli errori si segnalano con una **segnalazione** (*issue*) sul [repository GitHub](https://github.com/BilanciaCivica/bilancia-civica/issues) indicando: pagina, affermazione, fonte corretta e data. Per contestare un contenuto usa il modello [Richiesta di rettifica](https://github.com/BilanciaCivica/bilancia-civica/issues/new?template=rettifica.md). Le segnalazioni sono pubbliche: non inserire dati personali, tuoi o di altre persone. Le correzioni vengono registrate con data e motivo in [CORREZIONI.md](CORREZIONI.md) (vedi [METODOLOGIA, §1.10](METODOLOGIA.md#110-registro-correzioni)).

Non serve saper programmare: basta un account GitHub gratuito. Le proposte di modifica (*pull request*) vengono accolte solo dopo la revisione dei manutentori.

## Licenza

Contribuendo accetti che i tuoi **testi** siano rilasciati con licenza [CC BY-SA 4.0](LICENSE-TESTI) e il tuo **codice** con licenza [AGPL-3.0](LICENSE). Contribuisci solo con materiale tuo, con testi di atti ufficiali o con brevi citazioni di terzi indicate con la fonte.
