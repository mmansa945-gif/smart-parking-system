pipeline {
  agent any
  stages {
    stage('Test') { steps { sh 'python3 -m venv .venv && .venv/bin/pip install -r requirements.txt && .venv/bin/python -m pytest --cov=app --cov-fail-under=80' } }
    stage('Build') { steps { sh 'docker build -t goalguard .' } }
  }
}
