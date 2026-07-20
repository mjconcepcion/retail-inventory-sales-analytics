@echo off
rem Launches the private analytics dashboard at http://localhost:8502
cd /d "%~dp0"
.venv\Scripts\python.exe -m streamlit run dashboard\private_app.py --server.port 8502 --server.headless true
