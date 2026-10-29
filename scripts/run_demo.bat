@echo off
rem Starts the Placement Matcher demo. Everything (models, caches) stays on D:.
setlocal
set OLLAMA_MODELS=D:\ai-cache\ollama
set HF_HOME=D:\ai-cache\hf
set SENTENCE_TRANSFORMERS_HOME=D:\ai-cache\hf\sentence-transformers
set TORCH_HOME=D:\ai-cache\torch
set PIP_CACHE_DIR=D:\ai-cache\pip
set PYTHONUTF8=1
cd /d "%~dp0.."

powershell -NoProfile -Command "try { Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 http://127.0.0.1:11434/api/tags | Out-Null; exit 0 } catch { exit 1 }"
if errorlevel 1 (
  echo.
  echo [!] Ollama does not answer on port 11434.
  echo     Start it in a separate window:   set OLLAMA_MODELS=D:\ai-cache\ollama ^&^& ollama serve
  echo     The demo opens anyway: sample requirements run from the cache, custom requirements are disabled.
  echo.
)

call .venv\Scripts\activate.bat
streamlit run app\app.py
endlocal
