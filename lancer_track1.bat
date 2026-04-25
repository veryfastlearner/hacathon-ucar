@echo off
chcp 65001 > nul
echo ========================================================
echo   UCAR DataHub - Track 1: Document-to-KPI Engine
echo ========================================================
echo.

cd /d "%~dp0"

IF NOT EXIST "venv\Scripts\activate.bat" (
    echo [1/3] Creation de l'environnement virtuel...
    py -m venv venv
    if errorlevel 1 (
        echo [ERREUR] Impossible de creer l'environnement. Verifiez que Python est installe.
        pause
        exit /b
    )
) ELSE (
    echo [1/3] Environnement virtuel pret.
)

echo [2/3] Verification des dependances...
call venv\Scripts\activate.bat
echo Lancement de pip install (si ca bloque longtemps, c'est votre connexion internet)...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERREUR] Impossible d'installer les dependances. Verifiez votre connexion proxy ou internet.
    pause
    exit /b
)

echo.
echo [3/3] Execution du pipeline d'extraction PDF / Excel...
echo --------------------------------------------------------
py run_process_all.py
echo --------------------------------------------------------

echo.
echo ========================================================
echo.
set /p launch_api="Voulez-vous demarrer le serveur API Backend (FastAPI) maintenant ? (O/N) : "
if /i "%launch_api%"=="O" (
    echo.
    echo Demarrage de l'API sur http://127.0.0.1:8000/docs
    cd backend
    uvicorn app.main:app --reload
) else (
    echo Fermeture du lanceur. Au revoir !
)

pause
