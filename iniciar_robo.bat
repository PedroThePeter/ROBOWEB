@echo off
title Laboratorio do Robo Lotofacil V8.1
color 0A

echo ========================================================
echo   Inicializando o Robo da Lotofacil (Modo 100%% Local)
echo   Ambiente: V8.1 (5 Juizes e 3 Curadores)
echo ========================================================
echo.

:: 1. Ativa o ambiente virtual e inicia a API (Backend) em janela minimizada
echo [1/3] Acordando os Curadores e Juizes (Backend API)...
start "Backend API" /min cmd /c ".\venv\Scripts\activate && python main.py"

:: Aguarda 3 segundos para o servidor Python estabilizar
timeout /t 3 /nobreak > NUL

:: 2. Inicia o painel visual (Frontend React) em janela minimizada
echo [2/3] Ligando o Painel de Controle Visual (Frontend React)...
start "Frontend React" /min cmd /c "cd frontend && npm run dev"

:: Aguarda 4 segundos para o servidor Vite compilar a interface
timeout /t 4 /nobreak > NUL

:: 3. Abre o navegador padrão diretamente no sistema
echo [3/3] Abrindo o seu Laboratorio no Navegador...
start http://localhost:5173

echo.
echo ========================================================
echo [ OK ] Sistema iniciado e operante!
echo O robo ja esta aberto no seu navegador.
echo ========================================================
echo.
echo As engrenagens (terminais) estao rodando minimizadas.
echo Quando terminar de usar, basta fechar as janelas pretas abertas na barra de tarefas.
echo.
pause