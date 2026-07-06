pipeline {
    agent any

    triggers {
        cron('H */6 * * *')
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '15'))
        timeout(time: 20, unit: 'MINUTES')
    }

    stages {
        // On exécute tout le process Python d'un coup dans le conteneur officiel python:3.12-slim
        stage('Pipeline Exec') {
            steps {
                sh 'docker run --rm -v "$(pwd):/app" -w /app python:3.12-slim bash -lc "pip install -r requirements.txt && python scraper.py && python html_generator.py"'
            }
        }

        // On garde la détection de changements pour Jenkins
        stage('DetectChanges') {
            steps {
                script {
                    def prev = 'data/jobs_previous.csv'
                    if (!fileExists(prev)) {
                        echo "Pas d'extraction precedente : on considere qu'il y a du nouveau."
                        env.HAS_CHANGES = 'true'
                    } else {
                        def cur  = sh(script: "sha256sum data/jobs.csv | cut -d' ' -f1", returnStdout: true).trim()
                        def old  = sh(script: "sha256sum ${prev} | cut -d' ' -f1", returnStdout: true).trim()
                        env.HAS_CHANGES = (cur == old) ? 'false' : 'true'
                    }

                    if (env.HAS_CHANGES == 'true') {
                        echo 'Changements detectes : sauvegarde de la reference.'
                        sh 'cp data/jobs.csv data/jobs_previous.csv'
                    } else {
                        echo 'Aucune nouvelle offre : fin du traitement.'
                    }
                }
            }
        }

        // Validation rapide via Docker
        stage('Tests') {
            when { environment name: 'HAS_CHANGES', value: 'true' }
            steps {
                sh '''docker run --rm -v "$(pwd):/app" -w /app python:3.12-slim python - <<'PY'
import csv, re, sys

with open("data/jobs.csv", encoding="utf-8") as f:
    rows = list(csv.reader(f))
data_rows = max(len(rows) - 1, 0)
print(f"jobs.csv : {data_rows} lignes de donnees")
if data_rows < 10:
    sys.exit(1)

with open("public/index.html", encoding="utf-8") as f:
    html = f.read()
if "<table" not in html:
    sys.exit(1)

print("Tests OK")
PY
'''
            }
        }

        stage('Archive') {
            when { environment name: 'HAS_CHANGES', value: 'true' }
            steps {
                archiveArtifacts artifacts: 'data/jobs.csv, public/index.html', fingerprint: true, allowEmptyArchive: true
            }
        }

        stage('Deploy') {
            when { environment name: 'HAS_CHANGES', value: 'true' }
            steps {
                publishHTML(target: [
                    reportDir: 'public',
                    reportFiles: 'index.html',
                    reportName: 'Offres d emploi',
                    keepAll: true,
                    allowMissing: false,
                    alwaysLinkToLastBuild: true
                ])
            }
        }
    }

    post {
        success { echo "Pipeline OK." }
        failure { echo 'Echec du pipeline.' }
    }
}