REM Nuru wanted to be in this comment.
REM You'll have to change the location of Docker Desktop if you have it in a different location. Also this guy won't work at all  if you use Linux. Sorry.

@echo off

REM Start Docker engine
echo Starting Docker engine...
start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe" --background

REM Wait for Docker to start
:CHECK_DOCKER
timeout /t 2 /nobreak >nul
docker info >nul 2>&1
if errorlevel 1 goto CHECK_DOCKER

REM echo Starting LlamaGPT webserver
REM cd llama-gpt
REM start ./run.sh --model 13b --with-cuda
REM cd ..

echo Starting GlitchOS...
python bot.py

echo Batch script completed.
pause