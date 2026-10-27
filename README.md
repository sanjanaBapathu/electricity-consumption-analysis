# Electricity Consumption Analysis System

A Flask + MySQL educational web application for recording meter readings and analyzing electricity usage.

## Features
- Manage consumers and meters
- Record dated cumulative readings in kWh
- Calculate consumption between consecutive readings
- Flag possible meter resets/rollovers (decreasing readings)
- Monthly/yearly reports, high-usage list, validation report, chart, CSV export

## Run on Windows / VS Code
1. Install Python 3.10+ and MySQL Server. Start MySQL.
2. Extract the ZIP and open this folder in VS Code.
3. In PowerShell terminal:
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
   If activation is blocked:
   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
   .\.venv\Scripts\Activate.ps1
   ```
4. Install packages:
   ```powershell
   pip install -r requirements.txt
   ```
5. Copy settings and edit your MySQL password:
   ```powershell
   Copy-Item .env.example .env
   ```
   Open `.env`; update `DB_USER` and `DB_PASSWORD`. Do not share or upload `.env`.
6. Create the database/tables:
   ```powershell
   python init_db.py
   ```
7. Start the web app:
   ```powershell
   python app.py
   ```
8. Open http://127.0.0.1:5000 in your browser.

## First use
Add a consumer, then a meter, then at least two readings for that meter on different dates. A first reading has no usage interval. Usage is the difference between consecutive cumulative readings. A decreasing value is flagged and excluded from normal totals; the app does not guess a meter rollover modulus.

## Sample data
`sample_data.csv` gives sample values you can enter manually through the UI. This initial version does not import the CSV automatically.

## Push to GitHub
Create an empty repository on GitHub. In the project folder's terminal:
```powershell
git init
git add .
git status
git commit -m "Initial commit: electricity consumption analysis system"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/electricity-consumption-analysis.git
git push -u origin main
```
Replace `YOUR-USERNAME` with your GitHub username. Complete GitHub browser sign-in if prompted. Confirm `.env` is not listed by `git status`.

Later updates:
```powershell
git add .
git commit -m "Describe your update"
git push
```

## Troubleshooting
- MySQL connection error: start MySQL and verify `.env` credentials/port.
- Unknown database/tables: run `python init_db.py`.
- Missing package: activate `.venv`, then `pip install -r requirements.txt`.
- Port in use: change the port in the final `app.run(...)` line.
- These reports are analytical estimates, not official electricity billing calculations.
