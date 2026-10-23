# Bilancia Civica

**Ogni decreto, pesato sulla tua vita.**

Diritti, decreti e soldi pubblici: che cosa cambia per te, con le fonti.

- **Sito:** https://bilanciacivica.github.io/bilancia-civica/
- **Codice sorgente:** https://github.com/BilanciaCivica/bilancia-civica
- **Segnalazioni:** https://github.com/BilanciaCivica/bilancia-civica/issues (richieste di rettifica: https://github.com/BilanciaCivica/bilancia-civica/issues/new?template=rettifica.md)
- **Chi siamo e contatti:** https://bilanciacivica.github.io/bilancia-civica/chi-siamo.html
- **Note legali e privacy:** https://bilanciacivica.github.io/bilancia-civica/note-legali.html

Bilancia Civica è un progetto civico **apartitico** e **open source** che spiega in modo
semplice tre cose:

1. **Bussola Diritti** – cosa dicono le regole su presidi, cortei e scioperi, e cosa cambia con il decreto sicurezza (D.L. 190/2026);
2. **Stato degli atti** – a che punto sono le norme che seguiamo (decreto, misure sull'autotrasporto, legge di bilancio);
3. **Impatto e alternative** – come una misura pubblica può toccare una persona o una famiglia, con il metodo dichiarato e le alternative discusse.

Il risultato è un sito statico di poche pagine HTML, leggibile anche senza JavaScript,
senza cookie, senza tracciamento e senza risorse esterne.

## Che cos'è e che cosa non è

| È | Non è |
| --- | --- |
| Una sintesi divulgativa basata su fonti primarie (Gazzetta Ufficiale, Normattiva, Camera, Senato, Corte costituzionale, MEF, UPB, ISTAT) | Una consulenza legale o fiscale |
| Un lavoro che separa fatti, stime e interpretazioni | Un sito di parte o di propaganda |
| Un progetto aperto: testi, metodo e codice sono pubblici e correggibili | Un servizio che raccoglie o salva dati degli utenti (nemmeno il simulatore, nemmeno in forma anonima) |

Per una situazione concreta rivolgiti a un avvocato, a un sindacato o a un'associazione per i diritti.

## Come leggere i contenuti

Ogni affermazione importante porta un'etichetta e un livello di certezza (Alta / Media / Bassa):

- **[FATTO]** – verificabile su una fonte primaria indicata;
- **[STIMA]** – solo per numeri, sempre come intervallo (minimo–massimo), con ipotesi e metodo dichiarati;
- **[INTERPRETAZIONE]** – una lettura ragionata, attribuita a chi la sostiene;
- **[DA VERIFICARE]** – un'informazione non ancora confermata su fonte primaria.

Il metodo completo è in [METODOLOGIA.md](METODOLOGIA.md).

## Struttura del repository

```
contenuti/        testi delle pagine del sito (Markdown)
docs/             documenti di approfondimento (Bussola completa, analisi del D.L. 190/2026)
static/           foglio di stile e icona
METODOLOGIA.md    metodo, etichette, fonti, registro correzioni
CONTRIBUTING.md   come contribuire
CORREZIONI.md     registro pubblico delle correzioni
build.py          generatore del sito (solo libreria standard Python)
.github/          modelli per le segnalazioni (rettifica, errore)
LICENSE           GNU AGPL-3.0 (codice)
LICENSE-TESTI     CC BY-SA 4.0 (testi originali)
```

## Anteprima locale

Serve solo Python 3.9 o successivo, senza dipendenze:

```
python3 build.py
python3 -m http.server 8000 --directory _site
```

Poi apri `http://localhost:8000` nel browser. La cartella `_site/` viene generata da `build.py`
ed è esclusa dal controllo di versione (`.gitignore`): non va inserita nel ramo `main`.

## Pubblicare su GitHub Pages

Il sito si pubblica **da un ramo `gh-pages`** che contiene **solo** il risultato di `build.py`,
cioè il contenuto di `_site/` (le pagine HTML, `style.css`, `favicon.svg` e il file `.nojekyll`).
Non serve nessun workflow di GitHub Actions.

Il ramo `main` **non** va usato come sorgente di Pages: GitHub mostrerebbe i file Markdown
del repository senza le protezioni previste dal sito (Content Security Policy, nessun referrer).

Prima pubblicazione:

```
python3 build.py
git worktree add --orphan -b gh-pages ../bilancia-civica-pages
cp -r _site/. ../bilancia-civica-pages/
cd ../bilancia-civica-pages
git add -A
git commit -m "Pubblica il sito"
git push origin gh-pages
```

Poi, nel repository su GitHub, apri **Settings → Pages** e scegli *Deploy from a branch*,
ramo `gh-pages`, cartella `/ (root)`. Il sito sarà su https://bilanciacivica.github.io/bilancia-civica/

Aggiornamenti successivi: rigenera con `python3 build.py`, svuota la cartella
`../bilancia-civica-pages` (tranne `.git`), copia di nuovo `_site/.`, quindi `git add -A`, `git commit` e `git push`.

Prima di pubblicare:

- aggiorna `AGGIORNATO` in `build.py` (la data mostrata nel piè di pagina) e le date nelle pagine modificate;
- se il repository ha un nome diverso da `bilancia-civica`, aggiorna `REPO_URL` in `build.py`.

## Contribuire e segnalare errori

Gli errori si segnalano aprendo una **segnalazione** (*issue*) su GitHub (https://github.com/BilanciaCivica/bilancia-civica/issues): indica la pagina, il testo da correggere,
la fonte corretta (preferibilmente primaria) e la data. Le correzioni accettate vengono registrate in
[CORREZIONI.md](CORREZIONI.md). Dettagli in [CONTRIBUTING.md](CONTRIBUTING.md).
Le segnalazioni sono pubbliche: non inserire dati personali, tuoi o di altre persone.

È prevista una **revisione esterna** dei contenuti da parte di un giurista e di un economista.
Stato: **da fare**.

## Licenza

- **Codice** (`build.py`, `static/`): **GNU Affero General Public License v3.0**, vedi [LICENSE](LICENSE).
- **Testi originali** (`contenuti/`, `docs/`, `METODOLOGIA.md`, `CORREZIONI.md` e i testi del sito): **Creative Commons Attribuzione – Condividi allo stesso modo 4.0** (CC BY-SA 4.0), vedi [LICENSE-TESTI](LICENSE-TESTI) e la [sintesi in italiano](https://creativecommons.org/licenses/by-sa/4.0/deed.it).
- **Esclusi:** i testi degli atti ufficiali, non protetti dal diritto d'autore (art. 5 L. 633/1941), e le citazioni di terzi, che restano dei rispettivi autori (art. 70 L. 633/1941).

Attribuzione suggerita: *Bilancia Civica – https://bilanciacivica.github.io/bilancia-civica/ – CC BY-SA 4.0*.

*Contenuti aggiornati al 23/10/2026.*
