@echo off
:: Garante que o script execute estritamente na pasta onde esta salvo
cd /d "%~dp0"

title Laboratorio do Robo Lotofacil V8.1
color 0A

echo ========================================================
echo   Iniciando o Robo da Lotofacil (Modo 100%% Local)
echo ========================================================
echo.

:: 1. Verifica se o ambiente virtual existe
if not exist "venv\Scripts\activate.bat" (
    echo [ERRO CRITICO] O ambiente virtual 'venv' nao foi encontrado!
    echo Certifique-se de que este arquivo esta na pasta correta.
    pause
    exit /b
)

:: 2. Inicia o Backend Python em uma janela separada e mantem aberta se houver erro
echo [1/2] Iniciando o Backend FastAPI (Python na porta 8000)...
start "Backend API - Lotofacil" cmd /k "call venv\Scripts\activate && python main.py"

:: Aguarda 4 segundos para o servidor Python estabilizar a porta 8000
timeout /t 4 /nobreak > NUL

:: 3. Inicia o Frontend React em outra janela separada
echo [2/2] Iniciando o Painel React (Vite na porta 5173)...
if not exist "frontend" (
    echo [ERRO] A pasta 'frontend' nao foi encontrada!
    pause
    exit /b
)
start "Frontend React - Lotofacil" cmd /k "cd frontend && npm run dev"

:: Aguarda 3 segundos para o painel compilar
timeout /t 3 /nobreak > NUL

:: 4. Abre o navegador automaticamente
echo Abrindo o navegador no painel local...
start http://localhost:5173

echo.
echo ========================================================
echo   Automatizacao concluida com sucesso!
echo   Deixe as duas janelas pretas abertas em segundo plano.
echo ========================================================
pause