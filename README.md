# Sbobinator

Sbobinator è un'applicazione web avanzata per la trascrizione e il riassunto di file audio, utilizzando tecnologie all'avanguardia come OpenAI Whisper e AssemblyAI.

## Caratteristiche

- Trascrizione di file audio caricati localmente
- Supporto per l'elaborazione di audio da URL di YouTube e Google Drive
- Opzione di trascrizione con o senza separazione degli speaker (diarizzazione)
- Generazione automatica di riassunti delle trascrizioni
- Supporto multilingua (Italiano, Inglese, Francese, Tedesco, Spagnolo)

## Requisiti

- Python 3.7+
- Pip (gestore di pacchetti Python)

## Installazione

1. Clona il repository:
   ```
   git clone https://github.com/tuousername/sbobinator.git
   cd sbobinator
   ```

2. Crea un ambiente virtuale (opzionale ma consigliato):
   ```
   python -m venv venv
   source venv/bin/activate  # Per Linux/macOS
   venv\Scripts\activate  # Per Windows
   ```

3. Installa le dipendenze:
   ```
   pip install -r requirements.txt
   ```

## Configurazione

1. Crea un account su [OpenAI](https://openai.com/) e [AssemblyAI](https://www.assemblyai.com/) per ottenere le API key necessarie.

2. Configura le API key nell'applicazione tramite l'interfaccia di configurazione.

## Utilizzo

1. Avvia l'applicazione:
   ```
   streamlit run home.py
   ```

2. Apri il browser e vai all'indirizzo indicato nel terminale (solitamente `http://localhost:8501`).

3. Carica un file audio o inserisci un URL di YouTube/Google Drive.

4. Seleziona le opzioni di trascrizione desiderate e clicca su "Trascrivi".

5. Visualizza la trascrizione e il riassunto generato.

## Contribuire

Siamo aperti a contributi! Se hai suggerimenti per migliorare Sbobinator, non esitare a aprire una issue o inviare una pull request.

## Licenza

Questo progetto è distribuito sotto la licenza Apache 2.0. Vedi il file `LICENSE` per maggiori dettagli.

---

Creato da Tommaso Minuto
