# Progetto WhisperX

Questo progetto utilizza [WhisperX](https://github.com/m-bain/whisperX) per la trascrizione e l'allineamento avanzato dell'audio, con supporto per GPU (CUDA).

## Installazione Automatica

Per installare automaticamente tutte le dipendenze, utilizza `uv` (fortemente consigliato per la sua velocità):

1. **Clona o copia questo progetto** nella cartella desiderata.
2. **Crea l'ambiente virtuale e installa i requisiti** aprendo il terminale nella cartella del progetto ed eseguendo:
   ```powershell
   uv venv .venv-whisperx
   uv pip install -r requirements.txt -p .\.venv-whisperx
   ```

> **Nota per problemi di percorso:** Se sposti la cartella del progetto in futuro, esegui nuovamente il comando `uv pip install --reinstall-package whisperx -p .\.venv-whisperx` per correggere i collegamenti di Windows.

## Come usare WhisperX

Abbiamo predisposto degli script pronti all'uso per semplificare l'avvio senza dover attivare manualmente l'ambiente:

### 1. Trascrizione Standard
```powershell
.\whisperx.cmd nome_file_audio.mp3
```

### 2. Trascrizione Ottimizzata per GPU (Consigliato)
```powershell
.\whisperx-gpu.cmd nome_file_audio.mp3
```

### 3. Interfaccia Grafica (Frontend)
Per avviare l'interfaccia web e caricare i file dal browser:
```powershell
.\start_whisperx_frontend.cmd
```
L'interfaccia sarà accessibile tramite il browser all'indirizzo che comparirà nel terminale (es. http://127.0.0.1:8765).

## File e Cartelle
- `.venv-whisperx/`: Ambiente virtuale isolato (ignorato da git).
- `requirements.txt`: Elenco di tutte le dipendenze per ricreare l'ambiente.
- `.gitignore`: Evita di caricare su repository file temporanei, log o pesanti.
- `.cache/`: Cache locale dei modelli scaricati.
