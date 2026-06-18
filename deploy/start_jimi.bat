@echo off
:: 1. Inicia o Ollama (caminho padrão, ajuste se necessário)
echo Iniciando Ollama...
start "" "C:\Users\pedro\AppData\Local\Programs\Ollama\ollama app.exe"
timeout /t 10 /nobreak

:: 2. Inicia o Túnel Cloudflare em background
echo Iniciando Túnel Cloudflare...
start /min cmd /c "cloudflared tunnel --url http://localhost:5000"

:: 3. Inicia o JIMI
echo Iniciando sistema JIMI...
cd /d "C:\Users\pedro\OneDrive\Desktop\JIMI"
python jimi.py