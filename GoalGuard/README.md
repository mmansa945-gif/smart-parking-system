# GoalGuard: Personal Finance Goal Planner
Educational single-user prototype using FastAPI, SQLite, React (CDN) and NumPy. No financial advice. No login or production deployment.

## Windows PowerShell
```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```
Open http://127.0.0.1:8000 (internet needed for React CDN). API docs: http://127.0.0.1:8000/docs. Create a goal, add contributions, assess risk, project a range, refresh monitoring.

## Test (new terminal in project directory)
```powershell
.\.venv\Scripts\python.exe -m pytest -v --cov=app --cov-report=term-missing --cov-fail-under=80
```
## GitHub
For an empty remote: `git init`, `git add .`, `git commit -m "Build GoalGuard finance planner"`, `git branch -M main`, `git remote add origin https://github.com/mmansa945-gif/-GoalGuard-Personal-Finance-Goal-Planner.git`, `git push -u origin main`. For an existing remote, clone it first and copy project files into the clone (do not overwrite its .git directory), then commit and push.

## Docker
`docker build -t goalguard .` then `docker run --rm -p 8000:8000 goalguard` (database inside container is temporary).

## Evidence
`docs/` contains report, executed API tests and sample API output. CI/Jenkins definitions are supplied but not executed remotely. Browser UI, Selenium, Jira, SonarQube, spreadsheet validation and human review remain to be verified. No fabricated screenshots or results.
