import pytest
from fastapi.testclient import TestClient
from app.main import app
@pytest.fixture
def c(tmp_path,monkeypatch):
    monkeypatch.setenv('GOAL_DB',str(tmp_path/'test.db'))
    return TestClient(app)
def goal(c): return c.post('/api/goals',json={'name':'Emergency','target':100000,'months':24}).json()['id']
def test_health(c): assert c.get('/api/health').json()['status']=='ok'
def test_create(c): assert goal(c)==1
def test_empty(c): assert c.get('/api/goals').json()==[]
@pytest.mark.parametrize('field,value',[('name',''),('target',0),('target',-1),('months',0),('months',601)])
def test_invalid_goal(c,field,value):
    d={'name':'Fund','target':100,'months':12};d[field]=value
    assert c.post('/api/goals',json=d).status_code==422
def test_contribution(c):
    i=goal(c); assert c.post(f'/api/goals/{i}/contributions',json={'amount':100}).json()['saved']==100
    assert c.post(f'/api/goals/{i}/contributions',json={'amount':50}).json()['saved']==150
@pytest.mark.parametrize('amount',[0,-100])
def test_bad_contribution(c,amount): assert c.post(f'/api/goals/{goal(c)}/contributions',json={'amount':amount}).status_code==422
def test_missing_goal(c): assert c.post('/api/goals/99/contributions',json={'amount':10}).status_code==404
@pytest.mark.parametrize('v,risk',[(1,'low'),(3,'medium'),(5,'high')])
def test_profile(c,v,risk):
    assert c.post('/api/profile',json=dict(horizon=v,tolerance=v,stability=v)).json()['risk']==risk
    assert c.get('/api/profile').json()['risk']==risk
def test_empty_profile(c): assert c.get('/api/profile').json()['risk'] is None
def test_invalid_profile(c): assert c.post('/api/profile',json=dict(horizon=6,tolerance=3,stability=3)).status_code==422
def test_range(c):
    i=goal(c); c.post(f'/api/goals/{i}/contributions',json={'amount':10000});p=c.post(f'/api/goals/{i}/projection',json={'monthly':3000,'risk':'medium'}).json()
    assert p['p10']<p['median']<p['p90']; assert p['baseline']==82000; assert 0<=p['probability']<=1
    assert 'not guaranteed' in p['disclaimer']
def test_zero(c):
    p=c.post(f'/api/goals/{goal(c)}/projection',json={'monthly':0,'risk':'low'}).json();assert p['p90']==0
@pytest.mark.parametrize('d',[{'monthly':-1,'risk':'low'},{'monthly':1,'risk':'unknown'}])
def test_invalid_projection(c,d): assert c.post(f'/api/goals/{goal(c)}/projection',json=d).status_code==422
def test_metrics(c):
    c.get('/api/health'); assert c.get('/api/metrics').json()['requests']>=1
def test_frontend(c): assert 'GoalGuard' in c.get('/').text
