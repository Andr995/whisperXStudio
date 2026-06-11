from __future__ import annotations

import argparse
import html
import json
import os
import shutil
import subprocess
import sys
import threading
import time
import uuid
import warnings
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

warnings.filterwarnings("ignore", category=DeprecationWarning)
import cgi


ROOT = Path(__file__).resolve().parent
VENV = ROOT / ".venv-whisperx"
WHISPERX_EXE = VENV / "Scripts" / "whisperx.exe"
FFMPEG_EXE = VENV / "Scripts" / "ffmpeg.exe"
APP_DIR = ROOT / "whisperx_frontend_data"
UPLOAD_DIR = APP_DIR / "uploads"
OUTPUT_ROOT = APP_DIR / "outputs"
STATIC_DIR = APP_DIR / "static"
SERVER_LOG = APP_DIR / "server.log"

JOBS: dict[str, "Job"] = {}
JOBS_LOCK = threading.Lock()


LANGUAGES = [
    ("", "Auto rilevamento"),
    ("it", "Italiano"),
    ("en", "Inglese"),
    ("es", "Spagnolo"),
    ("fr", "Francese"),
    ("de", "Tedesco"),
    ("pt", "Portoghese"),
    ("nl", "Olandese"),
    ("pl", "Polacco"),
    ("ro", "Rumeno"),
    ("uk", "Ucraino"),
    ("ru", "Russo"),
    ("ar", "Arabo"),
    ("zh", "Cinese"),
    ("ja", "Giapponese"),
    ("ko", "Coreano"),
    ("af", "Afrikaans"),
    ("am", "Amharic"),
    ("as", "Assamese"),
    ("az", "Azerbaijani"),
    ("ba", "Bashkir"),
    ("be", "Belarusian"),
    ("bg", "Bulgarian"),
    ("bn", "Bengali"),
    ("bo", "Tibetan"),
    ("br", "Breton"),
    ("bs", "Bosnian"),
    ("ca", "Catalan"),
    ("cs", "Czech"),
    ("cy", "Welsh"),
    ("da", "Danish"),
    ("el", "Greek"),
    ("et", "Estonian"),
    ("eu", "Basque"),
    ("fa", "Persian"),
    ("fi", "Finnish"),
    ("fo", "Faroese"),
    ("gl", "Galician"),
    ("gu", "Gujarati"),
    ("ha", "Hausa"),
    ("haw", "Hawaiian"),
    ("he", "Hebrew"),
    ("hi", "Hindi"),
    ("hr", "Croatian"),
    ("ht", "Haitian Creole"),
    ("hu", "Hungarian"),
    ("hy", "Armenian"),
    ("id", "Indonesian"),
    ("is", "Icelandic"),
    ("jw", "Javanese"),
    ("ka", "Georgian"),
    ("kk", "Kazakh"),
    ("km", "Khmer"),
    ("kn", "Kannada"),
    ("la", "Latin"),
    ("lb", "Luxembourgish"),
    ("ln", "Lingala"),
    ("lo", "Lao"),
    ("lt", "Lithuanian"),
    ("lv", "Latvian"),
    ("mg", "Malagasy"),
    ("mi", "Maori"),
    ("mk", "Macedonian"),
    ("ml", "Malayalam"),
    ("mn", "Mongolian"),
    ("mr", "Marathi"),
    ("ms", "Malay"),
    ("mt", "Maltese"),
    ("my", "Burmese"),
    ("ne", "Nepali"),
    ("nn", "Nynorsk"),
    ("no", "Norwegian"),
    ("oc", "Occitan"),
    ("pa", "Panjabi"),
    ("ps", "Pashto"),
    ("sa", "Sanskrit"),
    ("sd", "Sindhi"),
    ("si", "Sinhala"),
    ("sk", "Slovak"),
    ("sl", "Slovenian"),
    ("sn", "Shona"),
    ("so", "Somali"),
    ("sq", "Albanian"),
    ("sr", "Serbian"),
    ("su", "Sundanese"),
    ("sv", "Swedish"),
    ("sw", "Swahili"),
    ("ta", "Tamil"),
    ("te", "Telugu"),
    ("tg", "Tajik"),
    ("th", "Thai"),
    ("tk", "Turkmen"),
    ("tl", "Tagalog"),
    ("tr", "Turkish"),
    ("tt", "Tatar"),
    ("ur", "Urdu"),
    ("uz", "Uzbek"),
    ("vi", "Vietnamese"),
    ("yi", "Yiddish"),
    ("yo", "Yoruba"),
    ("yue", "Cantonese"),
]


INDEX_HTML = r"""<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>WhisperX Studio</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f7f8fb;
      --surface: #ffffff;
      --surface-soft: #f1f4f8;
      --text: #172033;
      --muted: #667085;
      --line: #d8dee8;
      --primary: #176b87;
      --primary-dark: #0f5268;
      --accent: #b54708;
      --ok: #177245;
      --danger: #b42318;
      --shadow: 0 16px 40px rgba(16, 24, 40, .08);
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: "Segoe UI", Arial, sans-serif;
      font-size: 15px;
      line-height: 1.45;
    }

    header {
      background: #102a43;
      color: #fff;
      padding: 18px 24px;
      border-bottom: 4px solid #f4b740;
    }

    header h1 {
      margin: 0;
      font-size: 22px;
      font-weight: 700;
      letter-spacing: 0;
    }

    header p {
      margin: 4px 0 0;
      color: #d9e2ec;
      max-width: 980px;
    }

    main {
      max-width: 1280px;
      margin: 0 auto;
      padding: 24px;
      display: grid;
      grid-template-columns: minmax(0, 1fr) 390px;
      gap: 20px;
      align-items: start;
    }

    section, aside {
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: var(--shadow);
    }

    .panel {
      padding: 18px;
    }

    .dropzone {
      display: grid;
      place-items: center;
      min-height: 160px;
      border: 2px dashed #9aa7b8;
      border-radius: 8px;
      background: #f8fafc;
      padding: 22px;
      text-align: center;
      cursor: pointer;
      transition: border-color .16s ease, background .16s ease;
    }

    .dropzone.is-dragging {
      border-color: var(--primary);
      background: #e6f4f7;
    }

    .dropzone strong {
      display: block;
      font-size: 18px;
      margin-bottom: 6px;
    }

    .dropzone span {
      color: var(--muted);
    }

    input[type="file"] {
      position: absolute;
      width: 1px;
      height: 1px;
      overflow: hidden;
      opacity: 0;
    }

    .file-name {
      margin-top: 10px;
      color: var(--primary-dark);
      font-weight: 600;
      word-break: break-word;
    }

    .tabs {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin: 18px 0 12px;
      border-bottom: 1px solid var(--line);
      padding-bottom: 10px;
    }

    .tab {
      border: 1px solid var(--line);
      background: var(--surface-soft);
      color: var(--text);
      min-height: 38px;
      padding: 7px 12px;
      border-radius: 6px;
      cursor: pointer;
      font-weight: 600;
    }

    .tab.active {
      background: var(--primary);
      border-color: var(--primary);
      color: white;
    }

    .tab-panel {
      display: none;
    }

    .tab-panel.active {
      display: block;
    }

    .grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 14px;
    }

    .grid.three {
      grid-template-columns: repeat(3, minmax(0, 1fr));
    }

    .field {
      display: flex;
      flex-direction: column;
      gap: 6px;
      min-width: 0;
    }

    .field.full {
      grid-column: 1 / -1;
    }

    label {
      font-weight: 650;
      color: #26364d;
      font-size: 13px;
    }

    .hint {
      color: var(--muted);
      font-size: 12px;
      min-height: 16px;
    }

    input, select, textarea {
      width: 100%;
      border: 1px solid #b8c1cf;
      border-radius: 6px;
      background: #fff;
      color: var(--text);
      min-height: 38px;
      padding: 8px 10px;
      font: inherit;
    }

    textarea {
      min-height: 82px;
      resize: vertical;
    }

    .check-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 8px 12px;
    }

    .check {
      display: flex;
      align-items: center;
      gap: 8px;
      min-height: 34px;
      padding: 6px 8px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fff;
    }

    .check input {
      width: 18px;
      height: 18px;
      min-height: 18px;
      accent-color: var(--primary);
    }

    .check label {
      font-size: 13px;
      font-weight: 600;
      margin: 0;
    }

    .actions {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-top: 18px;
      padding-top: 14px;
      border-top: 1px solid var(--line);
    }

    button.primary, button.secondary, button.danger {
      border: 0;
      border-radius: 6px;
      min-height: 42px;
      padding: 9px 14px;
      cursor: pointer;
      font-weight: 700;
    }

    button.primary {
      background: var(--primary);
      color: white;
    }

    button.primary:hover { background: var(--primary-dark); }

    button.secondary {
      background: #e8eef5;
      color: #26364d;
      border: 1px solid #c7d1df;
    }

    button.danger {
      background: #fee4e2;
      color: var(--danger);
      border: 1px solid #fda29b;
    }

    button:disabled {
      opacity: .55;
      cursor: not-allowed;
    }

    aside {
      position: sticky;
      top: 16px;
      overflow: hidden;
    }

    .status {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 12px;
    }

    .status-dot {
      width: 12px;
      height: 12px;
      border-radius: 999px;
      background: #98a2b3;
    }

    .status-dot.running { background: var(--accent); }
    .status-dot.done { background: var(--ok); }
    .status-dot.failed { background: var(--danger); }

    .command-preview {
      white-space: pre-wrap;
      word-break: break-word;
      background: #0f172a;
      color: #e2e8f0;
      border-radius: 6px;
      padding: 12px;
      font-family: Consolas, "Courier New", monospace;
      font-size: 12px;
      min-height: 96px;
      max-height: 190px;
      overflow: auto;
    }

    .log {
      white-space: pre-wrap;
      word-break: break-word;
      background: #111827;
      color: #d1d5db;
      border-radius: 6px;
      padding: 12px;
      font-family: Consolas, "Courier New", monospace;
      font-size: 12px;
      min-height: 260px;
      max-height: 460px;
      overflow: auto;
    }

    .outputs {
      display: grid;
      gap: 8px;
      margin-top: 10px;
    }

    .outputs a {
      display: block;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 8px 10px;
      color: var(--primary-dark);
      text-decoration: none;
      background: #f8fafc;
      overflow-wrap: anywhere;
    }

    .pill {
      display: inline-flex;
      align-items: center;
      min-height: 26px;
      border-radius: 999px;
      padding: 3px 9px;
      background: #edf2f7;
      color: #344054;
      font-size: 12px;
      font-weight: 700;
    }

    @media (max-width: 1020px) {
      main {
        grid-template-columns: 1fr;
      }

      aside {
        position: static;
      }
    }

    @media (max-width: 720px) {
      main {
        padding: 14px;
      }

      .grid, .grid.three, .check-grid {
        grid-template-columns: 1fr;
      }

      .actions {
        align-items: stretch;
        flex-direction: column;
      }

      .actions button {
        width: 100%;
      }
    }
  </style>
</head>
<body>
  <header>
    <h1>WhisperX Studio</h1>
    <p>Trascina un audio o video, scegli le opzioni, avvia la trascrizione e scarica i risultati.</p>
  </header>

  <main>
    <section class="panel">
      <form id="jobForm">
        <div id="dropzone" class="dropzone" tabindex="0">
          <input id="audio" name="audio" type="file" accept="audio/*,video/*,.mp3,.wav,.m4a,.mp4,.mov,.mkv,.aac,.flac,.ogg,.opus,.wma">
          <div>
            <strong>Trascina qui il file</strong>
            <span>oppure clicca per selezionarlo dal computer</span>
            <div id="fileName" class="file-name"></div>
          </div>
        </div>

        <div class="tabs" role="tablist">
          <button class="tab active" type="button" data-tab="base">Base</button>
          <button class="tab" type="button" data-tab="output">Output</button>
          <button class="tab" type="button" data-tab="align">Allineamento</button>
          <button class="tab" type="button" data-tab="vad">VAD</button>
          <button class="tab" type="button" data-tab="diarize">Speaker</button>
          <button class="tab" type="button" data-tab="decode">Decodifica</button>
          <button class="tab" type="button" data-tab="system">Sistema</button>
        </div>

        <div class="tab-panel active" data-panel="base">
          <div class="grid">
            <div class="field">
              <label for="model">Modello</label>
              <select id="model" name="model">
                <option value="tiny">tiny</option>
                <option value="base">base</option>
                <option value="small" selected>small</option>
                <option value="medium">medium</option>
                <option value="large-v1">large-v1</option>
                <option value="large-v2">large-v2</option>
                <option value="large-v3">large-v3</option>
              </select>
              <div class="hint">small e' un buon compromesso iniziale.</div>
            </div>

            <div class="field">
              <label for="language">Lingua</label>
              <select id="language" name="language">{{language_options}}</select>
              <div class="hint">Lascia Auto se non sei sicuro.</div>
            </div>

            <div class="field">
              <label for="device">Dispositivo</label>
              <select id="device" name="device">
                <option value="cuda" selected>cuda GPU</option>
                <option value="cpu">cpu</option>
              </select>
              <div class="hint">La RTX 3060 Ti usa cuda.</div>
            </div>

            <div class="field">
              <label for="compute_type">Precisione</label>
              <select id="compute_type" name="compute_type">
                <option value="default">default</option>
                <option value="float16" selected>float16</option>
                <option value="float32">float32</option>
                <option value="int8">int8</option>
              </select>
              <div class="hint">int8 riduce memoria, float16 e' veloce su GPU.</div>
            </div>

            <div class="field">
              <label for="task">Operazione</label>
              <select id="task" name="task">
                <option value="transcribe" selected>trascrivi</option>
                <option value="translate">traduci in inglese</option>
              </select>
            </div>

            <div class="field">
              <label for="batch_size">Batch size</label>
              <input id="batch_size" name="batch_size" type="number" min="1" max="64" step="1" value="8">
            </div>
          </div>
        </div>

        <div class="tab-panel" data-panel="output">
          <div class="grid">
            <div class="field">
              <label for="output_format">Formato output</label>
              <select id="output_format" name="output_format">
                <option value="all" selected>all</option>
                <option value="srt">srt</option>
                <option value="vtt">vtt</option>
                <option value="txt">txt</option>
                <option value="tsv">tsv</option>
                <option value="json">json</option>
                <option value="aud">aud</option>
              </select>
            </div>

            <div class="field">
              <label for="output_dir_name">Cartella di destinazione</label>
              <input id="output_dir_name" name="output_dir_name" value="trascrizioni">
              <div class="hint">Nome o percorso assoluto (es. C:\Video).</div>
            </div>

            <div class="field">
              <label for="log_level">Livello log</label>
              <select id="log_level" name="log_level">
                <option value="">default</option>
                <option value="debug">debug</option>
                <option value="info">info</option>
                <option value="warning">warning</option>
                <option value="error">error</option>
                <option value="critical">critical</option>
              </select>
            </div>

            <div class="field">
              <label for="verbose">Verbose</label>
              <select id="verbose" name="verbose">
                <option value="">default</option>
                <option value="True">True</option>
                <option value="False">False</option>
              </select>
            </div>
          </div>

          <div class="check-grid" style="margin-top: 14px;">
            <div class="check">
              <input id="print_progress" name="print_progress" type="checkbox" checked>
              <label for="print_progress">Mostra progresso</label>
            </div>
          </div>
        </div>

        <div class="tab-panel" data-panel="align">
          <div class="grid">
            <div class="field">
              <label for="align_model">Modello allineamento</label>
              <input id="align_model" name="align_model" placeholder="automatico">
            </div>

            <div class="field">
              <label for="interpolate_method">Interpolazione parole</label>
              <select id="interpolate_method" name="interpolate_method">
                <option value="nearest" selected>nearest</option>
                <option value="linear">linear</option>
                <option value="ignore">ignore</option>
              </select>
            </div>

            <div class="field">
              <label for="segment_resolution">Segmenti</label>
              <select id="segment_resolution" name="segment_resolution">
                <option value="sentence" selected>sentence</option>
                <option value="chunk">chunk</option>
              </select>
            </div>

            <div class="field">
              <label for="max_line_width">Max caratteri per riga</label>
              <input id="max_line_width" name="max_line_width" type="number" min="1" step="1" placeholder="vuoto">
            </div>

            <div class="field">
              <label for="max_line_count">Max righe per segmento</label>
              <input id="max_line_count" name="max_line_count" type="number" min="1" step="1" placeholder="vuoto">
            </div>
          </div>

          <div class="check-grid" style="margin-top: 14px;">
            <div class="check">
              <input id="no_align" name="no_align" type="checkbox">
              <label for="no_align">Disattiva allineamento</label>
            </div>
            <div class="check">
              <input id="return_char_alignments" name="return_char_alignments" type="checkbox">
              <label for="return_char_alignments">Allineamento caratteri</label>
            </div>
            <div class="check">
              <input id="highlight_words" name="highlight_words" type="checkbox">
              <label for="highlight_words">Evidenzia parole</label>
            </div>
          </div>
        </div>

        <div class="tab-panel" data-panel="vad">
          <div class="grid">
            <div class="field">
              <label for="vad_method">Metodo VAD</label>
              <select id="vad_method" name="vad_method">
                <option value="pyannote" selected>pyannote</option>
                <option value="silero">silero</option>
              </select>
            </div>

            <div class="field">
              <label for="chunk_size">Chunk size</label>
              <input id="chunk_size" name="chunk_size" type="number" min="1" step="1" value="30">
            </div>

            <div class="field">
              <label for="vad_onset">VAD onset</label>
              <input id="vad_onset" name="vad_onset" type="number" min="0" max="1" step="0.001" value="0.5">
            </div>

            <div class="field">
              <label for="vad_offset">VAD offset</label>
              <input id="vad_offset" name="vad_offset" type="number" min="0" max="1" step="0.001" value="0.363">
            </div>
          </div>
        </div>

        <div class="tab-panel" data-panel="diarize">
          <div class="grid">
            <div class="field">
              <label for="hf_token">Hugging Face token</label>
              <input id="hf_token" name="hf_token" type="password" autocomplete="off" value="qui va il token" placeholder="necessario per diarizzazione">
            </div>

            <div class="field">
              <label for="diarize_model">Modello diarizzazione</label>
              <input id="diarize_model" name="diarize_model" value="pyannote/speaker-diarization-community-1">
            </div>

            <div class="field">
              <label for="min_speakers">Min speaker</label>
              <input id="min_speakers" name="min_speakers" type="number" min="1" step="1" placeholder="vuoto">
            </div>

            <div class="field">
              <label for="max_speakers">Max speaker</label>
              <input id="max_speakers" name="max_speakers" type="number" min="1" step="1" placeholder="vuoto">
            </div>
          </div>

          <div class="check-grid" style="margin-top: 14px;">
            <div class="check">
              <input id="diarize" name="diarize" type="checkbox">
              <label for="diarize">Riconosci parlanti</label>
            </div>
            <div class="check">
              <input id="speaker_embeddings" name="speaker_embeddings" type="checkbox">
              <label for="speaker_embeddings">Speaker embeddings</label>
            </div>
          </div>
        </div>

        <div class="tab-panel" data-panel="decode">
          <div class="grid three">
            <div class="field">
              <label for="temperature">Temperature</label>
              <input id="temperature" name="temperature" value="0">
            </div>
            <div class="field">
              <label for="best_of">Best of</label>
              <input id="best_of" name="best_of" type="number" min="1" step="1" value="5">
            </div>
            <div class="field">
              <label for="beam_size">Beam size</label>
              <input id="beam_size" name="beam_size" type="number" min="1" step="1" value="5">
            </div>
            <div class="field">
              <label for="patience">Patience</label>
              <input id="patience" name="patience" type="number" min="0" step="0.1" value="1.0">
            </div>
            <div class="field">
              <label for="length_penalty">Length penalty</label>
              <input id="length_penalty" name="length_penalty" type="number" step="0.1" value="1.0">
            </div>
            <div class="field">
              <label for="fp16">FP16</label>
              <select id="fp16" name="fp16">
                <option value="">default</option>
                <option value="True">True</option>
                <option value="False">False</option>
              </select>
            </div>
            <div class="field">
              <label for="temperature_increment_on_fallback">Fallback temp</label>
              <input id="temperature_increment_on_fallback" name="temperature_increment_on_fallback" type="number" step="0.1" value="0.2">
            </div>
            <div class="field">
              <label for="compression_ratio_threshold">Compression threshold</label>
              <input id="compression_ratio_threshold" name="compression_ratio_threshold" type="number" step="0.1" value="2.4">
            </div>
            <div class="field">
              <label for="logprob_threshold">Logprob threshold</label>
              <input id="logprob_threshold" name="logprob_threshold" type="number" step="0.1" value="-1.0">
            </div>
            <div class="field">
              <label for="no_speech_threshold">No speech threshold</label>
              <input id="no_speech_threshold" name="no_speech_threshold" type="number" min="0" max="1" step="0.01" value="0.6">
            </div>
            <div class="field">
              <label for="suppress_tokens">Suppress tokens</label>
              <input id="suppress_tokens" name="suppress_tokens" value="-1">
            </div>
          </div>

          <div class="grid" style="margin-top: 14px;">
            <div class="field full">
              <label for="initial_prompt">Prompt iniziale</label>
              <textarea id="initial_prompt" name="initial_prompt" placeholder="parole, nomi propri, contesto utile"></textarea>
            </div>
            <div class="field full">
              <label for="hotwords">Hotwords</label>
              <textarea id="hotwords" name="hotwords" placeholder="termini da riconoscere meglio, separati da virgole"></textarea>
            </div>
          </div>

          <div class="check-grid" style="margin-top: 14px;">
            <div class="check">
              <input id="suppress_numerals" name="suppress_numerals" type="checkbox">
              <label for="suppress_numerals">Sopprimi numeri</label>
            </div>
            <div class="check">
              <input id="condition_on_previous_text" name="condition_on_previous_text" type="checkbox">
              <label for="condition_on_previous_text">Usa testo precedente</label>
            </div>
          </div>
        </div>

        <div class="tab-panel" data-panel="system">
          <div class="grid">
            <div class="field">
              <label for="device_index">Device index</label>
              <input id="device_index" name="device_index" type="number" min="0" step="1" value="0">
            </div>

            <div class="field">
              <label for="threads">Thread CPU</label>
              <input id="threads" name="threads" type="number" min="0" step="1" value="0">
            </div>

            <div class="field full">
              <label for="model_dir">Cartella modelli</label>
              <input id="model_dir" name="model_dir" placeholder="vuoto = default locale">
            </div>

            <div class="field full">
              <label for="extra_args">Argomenti extra</label>
              <input id="extra_args" name="extra_args" placeholder='es. --model_cache_only True'>
              <div class="hint">Utile per opzioni nuove o combinazioni molto specifiche.</div>
            </div>
          </div>

          <div class="check-grid" style="margin-top: 14px;">
            <div class="check">
              <input id="model_cache_only" name="model_cache_only" type="checkbox">
              <label for="model_cache_only">Solo modelli in cache</label>
            </div>
          </div>
        </div>

        <div class="actions">
          <span class="pill">WhisperX {{whisperx_version}}</span>
          <div>
            <button id="resetBtn" class="secondary" type="button">Reset</button>
            <button id="submitBtn" class="primary" type="submit">Avvia trascrizione</button>
          </div>
        </div>
      </form>
    </section>

    <aside class="panel">
      <div class="status">
        <span id="statusDot" class="status-dot"></span>
        <strong id="statusText">In attesa</strong>
      </div>

      <label>Comando</label>
      <div id="commandPreview" class="command-preview">Seleziona un file per vedere il comando.</div>

      <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 14px;">
        <label>Log</label>
        <button id="stopBtn" class="danger" type="button" disabled>Ferma</button>
      </div>
      <div id="log" class="log"></div>

      <label style="display:block; margin-top: 14px;">Risultati</label>
      <div id="outputs" class="outputs"></div>
    </aside>
  </main>

  <script>
    const form = document.getElementById('jobForm');
    const fileInput = document.getElementById('audio');
    const dropzone = document.getElementById('dropzone');
    const fileName = document.getElementById('fileName');
    const submitBtn = document.getElementById('submitBtn');
    const stopBtn = document.getElementById('stopBtn');
    const resetBtn = document.getElementById('resetBtn');
    const logBox = document.getElementById('log');
    const outputsBox = document.getElementById('outputs');
    const statusText = document.getElementById('statusText');
    const statusDot = document.getElementById('statusDot');
    const commandPreview = document.getElementById('commandPreview');
    let currentJobId = null;
    let pollTimer = null;

    function qs(name) {
      return form.elements[name];
    }

    function isChecked(name) {
      const el = qs(name);
      return el && el.checked;
    }

    function value(name) {
      const el = qs(name);
      if (!el) return '';
      return (el.value || '').trim();
    }

    function quoteArg(arg) {
      if (!arg) return '""';
      if (/[\s"]/.test(arg)) return '"' + arg.replace(/"/g, '\\"') + '"';
      return arg;
    }

    function collectArgs(forPreview) {
      const args = [];
      const file = fileInput.files[0];
      args.push(file ? (forPreview ? file.name : '__UPLOADED_FILE__') : '<file>');

      const pairs = [
        ['--model', value('model')],
        ['--device', value('device')],
        ['--device_index', value('device_index')],
        ['--batch_size', value('batch_size')],
        ['--compute_type', value('compute_type')],
        ['--output_format', value('output_format')],
        ['--task', value('task')],
        ['--language', value('language')],
        ['--interpolate_method', value('interpolate_method')],
        ['--vad_method', value('vad_method')],
        ['--vad_onset', value('vad_onset')],
        ['--vad_offset', value('vad_offset')],
        ['--chunk_size', value('chunk_size')],
        ['--temperature', value('temperature')],
        ['--best_of', value('best_of')],
        ['--beam_size', value('beam_size')],
        ['--patience', value('patience')],
        ['--length_penalty', value('length_penalty')],
        ['--suppress_tokens', value('suppress_tokens')],
        ['--temperature_increment_on_fallback', value('temperature_increment_on_fallback')],
        ['--compression_ratio_threshold', value('compression_ratio_threshold')],
        ['--logprob_threshold', value('logprob_threshold')],
        ['--no_speech_threshold', value('no_speech_threshold')],
        ['--segment_resolution', value('segment_resolution')],
        ['--threads', value('threads')]
      ];

      for (const [flag, val] of pairs) {
        if (val) args.push(flag, val);
      }

      const optionalPairs = [
        ['--model_dir', value('model_dir')],
        ['--align_model', value('align_model')],
        ['--min_speakers', value('min_speakers')],
        ['--max_speakers', value('max_speakers')],
        ['--diarize_model', value('diarize_model')],
        ['--initial_prompt', value('initial_prompt')],
        ['--hotwords', value('hotwords')],
        ['--fp16', value('fp16')],
        ['--verbose', value('verbose')],
        ['--log-level', value('log_level')],
        ['--max_line_width', value('max_line_width')],
        ['--max_line_count', value('max_line_count')]
      ];

      for (const [flag, val] of optionalPairs) {
        if (val) args.push(flag, val);
      }

      if (isChecked('model_cache_only')) args.push('--model_cache_only', 'True');
      if (isChecked('no_align')) args.push('--no_align');
      if (isChecked('return_char_alignments')) args.push('--return_char_alignments');
      if (isChecked('diarize')) args.push('--diarize');
      if (isChecked('speaker_embeddings')) args.push('--speaker_embeddings');
      if (isChecked('suppress_numerals')) args.push('--suppress_numerals');
      if (isChecked('condition_on_previous_text')) args.push('--condition_on_previous_text', 'True');
      if (isChecked('highlight_words')) args.push('--highlight_words', 'True');
      if (isChecked('print_progress')) args.push('--print_progress', 'True');
      if (value('hf_token')) args.push('--hf_token', '********');

      const extra = value('extra_args');
      if (extra) args.push(extra);
      return args;
    }

    function refreshPreview() {
      const args = collectArgs(true).map(quoteArg).join(' ');
      commandPreview.textContent = '.\\whisperx.cmd ' + args;
    }

    function setStatus(status, label) {
      statusText.textContent = label;
      statusDot.className = 'status-dot';
      if (status === 'running') statusDot.classList.add('running');
      if (status === 'done') statusDot.classList.add('done');
      if (status === 'failed' || status === 'stopped') statusDot.classList.add('failed');
    }

    function setFile(files) {
      if (!files || !files.length) return;
      fileInput.files = files;
      fileName.textContent = files[0].name;
      refreshPreview();
    }

    dropzone.addEventListener('click', () => fileInput.click());
    dropzone.addEventListener('keydown', (event) => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        fileInput.click();
      }
    });

    fileInput.addEventListener('change', () => {
      fileName.textContent = fileInput.files[0] ? fileInput.files[0].name : '';
      refreshPreview();
    });

    for (const eventName of ['dragenter', 'dragover']) {
      dropzone.addEventListener(eventName, (event) => {
        event.preventDefault();
        dropzone.classList.add('is-dragging');
      });
    }

    for (const eventName of ['dragleave', 'drop']) {
      dropzone.addEventListener(eventName, (event) => {
        event.preventDefault();
        dropzone.classList.remove('is-dragging');
      });
    }

    dropzone.addEventListener('drop', (event) => {
      setFile(event.dataTransfer.files);
    });

    document.querySelectorAll('.tab').forEach((tab) => {
      tab.addEventListener('click', () => {
        document.querySelectorAll('.tab').forEach((item) => item.classList.remove('active'));
        document.querySelectorAll('.tab-panel').forEach((item) => item.classList.remove('active'));
        tab.classList.add('active');
        document.querySelector(`[data-panel="${tab.dataset.tab}"]`).classList.add('active');
      });
    });

    form.addEventListener('input', refreshPreview);
    form.addEventListener('change', refreshPreview);

    resetBtn.addEventListener('click', () => {
      form.reset();
      fileInput.value = '';
      fileName.textContent = '';
      outputsBox.innerHTML = '';
      logBox.textContent = '';
      setStatus('idle', 'In attesa');
      refreshPreview();
    });

    stopBtn.addEventListener('click', async () => {
      if (!currentJobId) return;
      await fetch('/api/stop/' + encodeURIComponent(currentJobId), { method: 'POST' });
    });

    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      if (!fileInput.files[0]) {
        alert('Seleziona prima un file audio o video.');
        return;
      }

      submitBtn.disabled = true;
      stopBtn.disabled = false;
      outputsBox.innerHTML = '';
      logBox.textContent = '';
      setStatus('running', 'Caricamento file... 0%');

      const file = fileInput.files[0];
      const formData = new FormData(form);
      const metadata = {};
      for (const [key, value] of formData.entries()) {
        if (key !== 'audio') metadata[key] = value;
      }

      const xhr = new XMLHttpRequest();
      xhr.open('POST', '/api/jobs');
      xhr.setRequestHeader('Content-Type', 'application/octet-stream');
      xhr.setRequestHeader('X-Audio-Filename', encodeURIComponent(file.name));
      xhr.setRequestHeader('X-Job-Metadata', encodeURIComponent(JSON.stringify(metadata)));

      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) {
          const percent = Math.round((e.loaded / e.total) * 100);
          setStatus('running', `Caricamento file... ${percent}%`);
        }
      };

      xhr.onload = () => {
        try {
          const result = JSON.parse(xhr.responseText);
          if (xhr.status >= 200 && xhr.status < 300) {
            currentJobId = result.job_id;
            commandPreview.textContent = result.command;
            setStatus('running', 'Avvio trascrizione...');
            poll();
            pollTimer = window.setInterval(poll, 1500);
          } else {
            throw new Error(result.error || 'Errore avvio job');
          }
        } catch (error) {
          submitBtn.disabled = false;
          stopBtn.disabled = true;
          setStatus('failed', 'Errore');
          logBox.textContent = String(error.message || error);
        }
      };

      xhr.onerror = () => {
        submitBtn.disabled = false;
        stopBtn.disabled = true;
        setStatus('failed', 'Errore di rete');
        logBox.textContent = 'Impossibile connettersi al server.';
      };

      xhr.send(file);
    });

    async function poll() {
      if (!currentJobId) return;
      const response = await fetch('/api/jobs/' + encodeURIComponent(currentJobId));
      const job = await response.json();
      logBox.textContent = job.log || '';
      logBox.scrollTop = logBox.scrollHeight;

      const labels = {
        queued: 'In coda',
        running: 'Trascrizione in corso',
        done: 'Completato',
        failed: 'Errore',
        stopped: 'Fermato'
      };
      setStatus(job.status, labels[job.status] || job.status);

      outputsBox.innerHTML = '';
      for (const file of job.outputs || []) {
        const link = document.createElement('a');
        if (file.url) {
          link.href = file.url;
          link.target = '_blank';
        } else {
          link.href = '#';
          link.onclick = (e) => { e.preventDefault(); };
          link.style.cursor = 'default';
        }
        link.textContent = file.name;
        outputsBox.appendChild(link);
      }

      if (!['queued', 'running'].includes(job.status)) {
        window.clearInterval(pollTimer);
        submitBtn.disabled = false;
        stopBtn.disabled = true;
      }
    }

    refreshPreview();
  </script>
</body>
</html>
"""


class Job:
    def __init__(self, job_id: str, command: list[str], command_text: str, output_dir: Path):
        self.job_id = job_id
        self.command = command
        self.command_text = command_text
        self.output_dir = output_dir
        self.status = "queued"
        self.log_lines: list[str] = []
        self.process: subprocess.Popen[str] | None = None
        self.created_at = time.time()
        self.finished_at: float | None = None

    def append(self, text: str) -> None:
        with JOBS_LOCK:
            self.log_lines.append(text)
            if len(self.log_lines) > 1200:
                self.log_lines = self.log_lines[-1200:]

    @property
    def log(self) -> str:
        with JOBS_LOCK:
            return "".join(self.log_lines)


def ensure_dirs() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    STATIC_DIR.mkdir(parents=True, exist_ok=True)


def app_log(message: str) -> None:
    ensure_dirs()
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with SERVER_LOG.open("a", encoding="utf-8") as log_file:
        log_file.write(f"[{stamp}] {message}\n")


def safe_print(message: str) -> None:
    try:
        if sys.stdout:
            print(message, flush=True)
            return
    except Exception:
        pass
    app_log(message)


def safe_name(name: str, default: str = "file") -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in "._- " else "_" for ch in name).strip()
    cleaned = cleaned.strip(". ")
    return cleaned or default


def unique_path(directory: Path, filename: str) -> Path:
    target = directory / safe_name(filename)
    if not target.exists():
        return target
    stem = target.stem
    suffix = target.suffix
    for index in range(2, 10000):
        candidate = directory / f"{stem}_{index}{suffix}"
        if not candidate.exists():
            return candidate
    raise RuntimeError("Impossibile creare un nome file unico.")


def form_value(form: dict | cgi.FieldStorage, name: str, default: str = "") -> str:
    if isinstance(form, dict):
        return str(form.get(name, default)).strip()
    field = form.getfirst(name, default)
    if field is None:
        return default
    return str(field).strip()


def form_bool(form: dict | cgi.FieldStorage, name: str) -> bool:
    if isinstance(form, dict):
        val = form.get(name, "")
        return val not in ("", "False", "false", "0", False, None)
    return name in form and form.getfirst(name) not in ("", "False", "false", "0", None)


def add_pair(command: list[str], flag: str, value: str) -> None:
    if value:
        command.extend([flag, value])


def build_command(form: dict | cgi.FieldStorage, audio_path: Path, output_dir: Path) -> list[str]:
    command = [str(WHISPERX_EXE), str(audio_path)]

    core_pairs = [
        ("--model", form_value(form, "model", "small")),
        ("--device", form_value(form, "device", "cuda")),
        ("--device_index", form_value(form, "device_index", "0")),
        ("--batch_size", form_value(form, "batch_size", "8")),
        ("--compute_type", form_value(form, "compute_type", "float16")),
        ("--output_dir", str(output_dir)),
        ("--output_format", form_value(form, "output_format", "all")),
        ("--task", form_value(form, "task", "transcribe")),
        ("--language", form_value(form, "language")),
        ("--interpolate_method", form_value(form, "interpolate_method", "nearest")),
        ("--vad_method", form_value(form, "vad_method", "pyannote")),
        ("--vad_onset", form_value(form, "vad_onset", "0.5")),
        ("--vad_offset", form_value(form, "vad_offset", "0.363")),
        ("--chunk_size", form_value(form, "chunk_size", "30")),
        ("--temperature", form_value(form, "temperature", "0")),
        ("--best_of", form_value(form, "best_of", "5")),
        ("--beam_size", form_value(form, "beam_size", "5")),
        ("--patience", form_value(form, "patience", "1.0")),
        ("--length_penalty", form_value(form, "length_penalty", "1.0")),
        ("--suppress_tokens", form_value(form, "suppress_tokens", "-1")),
        ("--temperature_increment_on_fallback", form_value(form, "temperature_increment_on_fallback", "0.2")),
        ("--compression_ratio_threshold", form_value(form, "compression_ratio_threshold", "2.4")),
        ("--logprob_threshold", form_value(form, "logprob_threshold", "-1.0")),
        ("--no_speech_threshold", form_value(form, "no_speech_threshold", "0.6")),
        ("--segment_resolution", form_value(form, "segment_resolution", "sentence")),
        ("--threads", form_value(form, "threads", "0")),
    ]

    optional_pairs = [
        ("--model_dir", form_value(form, "model_dir")),
        ("--align_model", form_value(form, "align_model")),
        ("--min_speakers", form_value(form, "min_speakers")),
        ("--max_speakers", form_value(form, "max_speakers")),
        ("--diarize_model", form_value(form, "diarize_model")),
        ("--initial_prompt", form_value(form, "initial_prompt")),
        ("--hotwords", form_value(form, "hotwords")),
        ("--fp16", form_value(form, "fp16")),
        ("--verbose", form_value(form, "verbose")),
        ("--log-level", form_value(form, "log_level")),
        ("--max_line_width", form_value(form, "max_line_width")),
        ("--max_line_count", form_value(form, "max_line_count")),
    ]

    for flag, value in [*core_pairs, *optional_pairs]:
        add_pair(command, flag, value)

    if form_bool(form, "model_cache_only"):
        command.extend(["--model_cache_only", "True"])
    if form_bool(form, "no_align"):
        command.append("--no_align")
    if form_bool(form, "return_char_alignments"):
        command.append("--return_char_alignments")
    if form_bool(form, "diarize"):
        command.append("--diarize")
    if form_bool(form, "speaker_embeddings"):
        command.append("--speaker_embeddings")
    if form_bool(form, "suppress_numerals"):
        command.append("--suppress_numerals")
    if form_bool(form, "condition_on_previous_text"):
        command.extend(["--condition_on_previous_text", "True"])
    if form_bool(form, "highlight_words"):
        command.extend(["--highlight_words", "True"])
    if form_bool(form, "print_progress"):
        command.extend(["--print_progress", "True"])

    hf_token = form_value(form, "hf_token")
    if hf_token:
        command.extend(["--hf_token", hf_token])

    extra_args = form_value(form, "extra_args")
    if extra_args:
        command.extend(split_extra_args(extra_args))

    return command


def split_extra_args(extra_args: str) -> list[str]:
    import shlex

    return shlex.split(extra_args, posix=False)


def command_for_display(command: list[str]) -> str:
    visible = []
    hide_next = False
    for item in command:
        if hide_next:
            visible.append("********")
            hide_next = False
            continue
        visible.append(item)
        if item == "--hf_token":
            hide_next = True
    return subprocess.list2cmdline(visible)


def job_outputs(job: Job) -> list[dict[str, str]]:
    if not job.output_dir.exists():
        return []
    files = []
    for path in sorted(job.output_dir.glob("*")):
        if path.is_file():
            try:
                relative = path.relative_to(OUTPUT_ROOT)
                url = "/download/" + "/".join(relative.parts)
                name = path.name
            except ValueError:
                url = ""
                name = f"Salvato in: {path}"
            files.append({"name": name, "url": url})
    return files


def run_job(job: Job) -> None:
    env = os.environ.copy()
    env["PATH"] = str(VENV / "Scripts") + os.pathsep + env.get("PATH", "")
    env["HF_HOME"] = str(ROOT / ".cache" / "huggingface")
    env["XDG_CACHE_HOME"] = str(ROOT / ".cache")
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    with JOBS_LOCK:
        job.status = "running"

    job.append("Comando:\n")
    job.append(job.command_text + "\n\n")
    job.append("Avvio WhisperX...\n")

    try:
        job.process = subprocess.Popen(
            job.command,
            cwd=str(ROOT),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        assert job.process.stdout is not None
        for line in job.process.stdout:
            job.append(line)
        return_code = job.process.wait()
        with JOBS_LOCK:
            if job.status == "stopped":
                job.append("\nJob fermato dall'utente.\n")
            elif return_code == 0:
                job.status = "done"
                job.append("\nCompletato.\n")
            else:
                job.status = "failed"
                job.append(f"\nWhisperX terminato con codice {return_code}.\n")
            job.finished_at = time.time()
    except Exception as exc:
        with JOBS_LOCK:
            job.status = "failed"
            job.finished_at = time.time()
        job.append(f"\nErrore: {exc}\n")


def render_index() -> bytes:
    languages = "\n".join(
        f'<option value="{html.escape(code)}"{" selected" if code == "it" else ""}>{html.escape(label)}</option>'
        for code, label in LANGUAGES
    )
    version = whisperx_version()
    page = INDEX_HTML.replace("{{language_options}}", languages).replace(
        "{{whisperx_version}}", html.escape(version)
    )
    return page.encode("utf-8")


def whisperx_version() -> str:
    if not WHISPERX_EXE.exists():
        return "non trovato"
    try:
        result = subprocess.run(
            [str(WHISPERX_EXE), "--version"],
            cwd=str(ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=20,
            encoding="utf-8",
            errors="replace",
        )
        return result.stdout.strip() or "installato"
    except Exception:
        return "installato"


class Handler(BaseHTTPRequestHandler):
    server_version = "WhisperXFrontend/1.0"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self.send_bytes(render_index(), "text/html; charset=utf-8")
            return
        if parsed.path.startswith("/api/jobs/"):
            self.handle_get_job(parsed.path.rsplit("/", 1)[-1])
            return
        if parsed.path.startswith("/download/"):
            self.handle_download(parsed.path.removeprefix("/download/"))
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/jobs":
            self.handle_create_job()
            return
        if parsed.path.startswith("/api/stop/"):
            self.handle_stop_job(parsed.path.rsplit("/", 1)[-1])
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def handle_create_job(self) -> None:
        if not WHISPERX_EXE.exists():
            self.send_json({"error": f"WhisperX non trovato: {WHISPERX_EXE}"}, HTTPStatus.INTERNAL_SERVER_ERROR)
            return
        if not FFMPEG_EXE.exists():
            self.send_json({"error": f"ffmpeg non trovato: {FFMPEG_EXE}"}, HTTPStatus.INTERNAL_SERVER_ERROR)
            return

        content_type = self.headers.get("Content-Type", "")
        
        if content_type == "application/octet-stream":
            import json
            from urllib.parse import unquote
            
            audio_filename = unquote(self.headers.get("X-Audio-Filename", ""))
            metadata_str = unquote(self.headers.get("X-Job-Metadata", "{}"))
            try:
                form_data = json.loads(metadata_str)
            except json.JSONDecodeError:
                form_data = {}

            if not audio_filename:
                self.send_json({"error": "Nessun file ricevuto."}, HTTPStatus.BAD_REQUEST)
                return

            job_id = uuid.uuid4().hex[:12]
            upload_job_dir = UPLOAD_DIR / job_id
            upload_job_dir.mkdir(parents=True, exist_ok=True)
            upload_path = unique_path(upload_job_dir, audio_filename)

            length = int(self.headers.get("Content-Length", 0))
            if length > 0:
                bytes_left = length
                with upload_path.open("wb") as target:
                    while bytes_left > 0:
                        chunk_size = min(1024 * 1024 * 4, bytes_left)
                        chunk = self.rfile.read(chunk_size)
                        if not chunk:
                            break
                        target.write(chunk)
                        bytes_left -= len(chunk)
            else:
                self.send_json({"error": "File vuoto."}, HTTPStatus.BAD_REQUEST)
                return
        else:
            form_data = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={
                    "REQUEST_METHOD": "POST",
                    "CONTENT_TYPE": self.headers.get("Content-Type", ""),
                    "CONTENT_LENGTH": self.headers.get("Content-Length", "0"),
                },
            )

            file_item = form_data["audio"] if "audio" in form_data else None
            if file_item is None or not getattr(file_item, "filename", ""):
                self.send_json({"error": "Nessun file ricevuto."}, HTTPStatus.BAD_REQUEST)
                return

            job_id = uuid.uuid4().hex[:12]
            upload_job_dir = UPLOAD_DIR / job_id
            upload_job_dir.mkdir(parents=True, exist_ok=True)
            upload_path = unique_path(upload_job_dir, Path(file_item.filename).name)

            with upload_path.open("wb") as target:
                shutil.copyfileobj(file_item.file, target)

        raw_output_dir = form_value(form_data, "output_dir_name", "trascrizioni")
        if os.path.isabs(raw_output_dir):
            output_dir = Path(raw_output_dir) / f"{time.strftime('%Y%m%d-%H%M%S')}-{job_id}"
        else:
            output_name = safe_name(raw_output_dir, "trascrizioni")
            output_dir = OUTPUT_ROOT / f"{time.strftime('%Y%m%d-%H%M%S')}-{output_name}-{job_id}"
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            command = build_command(form_data, upload_path, output_dir)
        except Exception as exc:
            self.send_json({"error": f"Opzioni non valide: {exc}"}, HTTPStatus.BAD_REQUEST)
            return

        command_text = command_for_display(command)
        job = Job(job_id=job_id, command=command, command_text=command_text, output_dir=output_dir)
        with JOBS_LOCK:
            JOBS[job_id] = job
        thread = threading.Thread(target=run_job, args=(job,), daemon=True)
        thread.start()

        self.send_json({"job_id": job_id, "command": command_text})

    def handle_get_job(self, raw_job_id: str) -> None:
        job_id = unquote(raw_job_id)
        with JOBS_LOCK:
            job = JOBS.get(job_id)
        if job is None:
            self.send_json({"error": "Job non trovato."}, HTTPStatus.NOT_FOUND)
            return
        self.send_json(
            {
                "job_id": job.job_id,
                "status": job.status,
                "command": job.command_text,
                "log": job.log,
                "outputs": job_outputs(job),
            }
        )

    def handle_stop_job(self, raw_job_id: str) -> None:
        job_id = unquote(raw_job_id)
        with JOBS_LOCK:
            job = JOBS.get(job_id)
            if job is not None and job.status in ("queued", "running"):
                job.status = "stopped"
        if job is None:
            self.send_json({"error": "Job non trovato."}, HTTPStatus.NOT_FOUND)
            return
        if job.process is not None and job.process.poll() is None:
            job.process.terminate()
        self.send_json({"ok": True})

    def handle_download(self, raw_path: str) -> None:
        relative = Path(unquote(raw_path))
        target = (OUTPUT_ROOT / relative).resolve()
        try:
            target.relative_to(OUTPUT_ROOT.resolve())
        except ValueError:
            self.send_error(HTTPStatus.FORBIDDEN)
            return
        if not target.exists() or not target.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Length", str(target.stat().st_size))
        self.send_header("Content-Disposition", f'attachment; filename="{target.name}"')
        self.end_headers()
        with target.open("rb") as source:
            shutil.copyfileobj(source, self.wfile)

    def send_json(self, data: object, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_bytes(body, "application/json; charset=utf-8", status)

    def send_bytes(
        self,
        body: bytes,
        content_type: str,
        status: HTTPStatus = HTTPStatus.OK,
    ) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        message = "[%s] %s" % (self.log_date_time_string(), format % args)
        try:
            if sys.stderr:
                sys.stderr.write(message + "\n")
                return
        except Exception:
            pass
        app_log(message)


def main() -> int:
    parser = argparse.ArgumentParser(description="Frontend locale per WhisperX.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    ensure_dirs()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    safe_print(f"WhisperX Studio: http://{args.host}:{args.port}")
    safe_print("Premi Ctrl+C per fermare il server.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        safe_print("Server fermato.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        app_log(f"Errore fatale: {exc}")
        raise
