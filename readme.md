# Progetto WhisperX

Questo progetto utilizza [WhisperX](https://github.com/m-bain/whisperX) per la trascrizione e l'allineamento avanzato dell'audio, con supporto per GPU (CUDA).

## Installazione

1. **Clona o copia questo progetto** nella cartella desiderata.

2. **Crea l'ambiente virtuale:**
   ```powershell
   python -m venv .venv-whisperx
   ```

3. **Attiva l'ambiente virtuale:**
   ```powershell
   .\.venv-whisperx\Scripts\Activate.ps1
   ```

4. **Installa le dipendenze:**
   ```powershell
   pip install -r requirements.txt
   ```

> **Nota per problemi di percorso:** Se sposti la cartella del progetto in futuro, esegui nuovamente il comando `pip install --force-reinstall whisperx` con l'ambiente virtuale attivo per correggere i collegamenti.

## Come usare WhisperX

Sono disponibili degli script pronti all'uso per semplificare l'avvio senza dover attivare manualmente l'ambiente:

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

L'interfaccia sarà accessibile tramite il browser all'indirizzo che comparirà nel terminale (es. `http://127.0.0.1:8765`).

## File e Cartelle

| Percorso | Descrizione |
|---|---|
| `.venv-whisperx/` | Ambiente virtuale isolato (ignorato da git) |
| `requirements.txt` | Elenco di tutte le dipendenze per ricreare l'ambiente |
| `.gitignore` | Evita di caricare su repository file temporanei, log o pesanti |
| `.cache/` | Cache locale dei modelli scaricati |
