import os, sqlite3, time
from pathlib import Path
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

app = FastAPI(title='GoalGuard')
metrics = {'requests': 0, 'errors': 0, 'latency_ms_total': 0.0}
def db():
    c = sqlite3.connect(os.getenv('GOAL_DB', 'goals.db'))
    c.row_factory = sqlite3.Row
    c.execute('PRAGMA foreign_keys=ON')
    c.executescript('''CREATE TABLE IF NOT EXISTS goals(id INTEGER PRIMARY KEY, name TEXT NOT NULL, target REAL NOT NULL, months INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS contributions(id INTEGER PRIMARY KEY, goal_id INTEGER REFERENCES goals(id), amount REAL NOT NULL);
    CREATE TABLE IF NOT EXISTS profiles(id INTEGER PRIMARY KEY CHECK(id=1), score INTEGER, risk TEXT);''')
    return c
class Goal(BaseModel):
    name: str = Field(min_length=1,max_length=100)
    target: float = Field(gt=0, le=1e10)
    months: int = Field(ge=1, le=600)
class Contribution(BaseModel):
    amount: float = Field(gt=0, le=1e10)
class Profile(BaseModel):
    horizon: int = Field(ge=1,le=5)
    tolerance: int = Field(ge=1,le=5)
    stability: int = Field(ge=1,le=5)
class Projection(BaseModel):
    monthly: float = Field(ge=0,le=1e9)
    risk: str = Field(pattern='^(low|medium|high)$')
@app.middleware('http')
async def monitor(request, call_next):
    start=time.perf_counter()
    response=await call_next(request)
    metrics['requests']+=1
    metrics['errors']+=int(response.status_code>=400)
    metrics['latency_ms_total']+=(time.perf_counter()-start)*1000
    return response
@app.get('/api/health')
def health(): return {'status':'ok'}
@app.get('/api/metrics')
def get_metrics(): return {**metrics,'mean_latency_ms':metrics['latency_ms_total']/max(1,metrics['requests'])}
@app.post('/api/goals',status_code=201)
def create_goal(g:Goal):
    with db() as c:
        cur=c.execute('INSERT INTO goals(name,target,months) VALUES(?,?,?)',(g.name,g.target,g.months))
        return {'id':cur.lastrowid,**g.model_dump()}
@app.get('/api/goals')
def goals():
    with db() as c:
        return [dict(r) for r in c.execute('SELECT g.*, COALESCE(SUM(c.amount),0) saved FROM goals g LEFT JOIN contributions c ON g.id=c.goal_id GROUP BY g.id ORDER BY g.id')]
def get_goal(id):
    for g in goals():
        if g['id']==id: return g
    raise HTTPException(404,'Goal not found')
@app.post('/api/goals/{id}/contributions',status_code=201)
def contribute(id:int, item:Contribution):
    get_goal(id)
    with db() as c: c.execute('INSERT INTO contributions(goal_id,amount) VALUES(?,?)',(id,item.amount))
    return get_goal(id)
@app.post('/api/profile')
def profile(p:Profile):
    score=p.horizon+p.tolerance+p.stability
    risk='low' if score<=6 else 'medium' if score<=11 else 'high'
    with db() as c: c.execute('INSERT OR REPLACE INTO profiles VALUES(1,?,?)',(score,risk))
    return {'score':score,'risk':risk}
@app.get('/api/profile')
def read_profile():
    with db() as c:
        r=c.execute('SELECT score,risk FROM profiles WHERE id=1').fetchone()
        return dict(r) if r else {'score':None,'risk':None}
@app.post('/api/goals/{id}/projection')
def project(id:int,p:Projection):
    g=get_goal(id)
    mu,sigma={'low':(.03,.04),'medium':(.06,.10),'high':(.08,.18)}[p.risk]
    rng=np.random.default_rng(44)
    values=np.full(2000,float(g['saved']))
    for _ in range(g['months']):
        values=values*np.exp((mu-sigma*sigma/2)/12+sigma/np.sqrt(12)*rng.normal(size=2000))+p.monthly
    lo,mid,hi=np.percentile(values,[10,50,90])
    return {'p10':round(float(lo),2),'median':round(float(mid),2),'p90':round(float(hi),2),'probability':round(float(np.mean(values>=g['target'])),4),'baseline':round(g['saved']+p.monthly*g['months'],2),'disclaimer':'Illustrative estimates, not guaranteed or financial advice.'}
frontend=Path(__file__).resolve().parents[1]/'frontend'
app.mount('/',StaticFiles(directory=frontend,html=True),name='frontend')
