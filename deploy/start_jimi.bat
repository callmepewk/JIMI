@echo off
title Inicializacao JIMI
color 0b

echo =========================================
echo         INICIANDO O SISTEMA JIMI
echo =========================================
echo.

:: 1. Inicia o Ollama via Docker (A Prova de Falhas)
echo [1/3] Verificando servidor de IA (Ollama)...

:: Tenta ligar o container se ele ja existir (silenciosamente)
docker start ollama >nul 2>&1

:: Se der erro (porque nao existe ainda), ele cria um novo com o limite de 3GB
if %errorlevel% neq 0 (
    echo Criando novo container do Ollama com limite de 3GB...
    docker run -d --name ollama --memory="3g" -p 11434:11434 ollama/ollama
) else (
    echo Container 'ollama' ja existe e foi iniciado.
)

:: Aguarda menos tempo, o start de um container existente é muito rápido
timeout /t 5 /nobreak >nul

:: 2. Inicia o Tunel Cloudflare
echo.
echo [2/3] Abrindo conexao com o mundo exterior (Cloudflare)...
:: Mudado de /c para /k. A janela abre minimizada, mas se voce maximizar, o link estara la e a janela nao fecha sozinha.
start /min cmd /c "cloudflared tunnel --url http://localhost:5000 > cloudflared.log 2>&1"
timeout /t 3 /nobreak >nul

:: 3. Inicia o JIMI
echo.
echo [3/3] Acordando o JIMI...
cd /d "C:\Users\pedro\OneDrive\Desktop\JIMI"

:: Protecao: Se voce estiver usando um ambiente virtual (venv) do Python, ele ativa automaticamente
if exist "venv\Scripts\activate.bat" (
    echo Ativando ambiente virtual Python...
    call venv\Scripts\activate.bat
)

:: Executa a interface gráfica e o cérebro
python jimi.py

echo.
echo Sessao do JIMI encerrada.
pause