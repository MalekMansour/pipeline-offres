pipeline {
    agent any

    // Declenchement automatique : toutes les ~6 heures (H = repartition de la charge).
    // Combine au stage DetectChanges, on evite les executions inutiles.
    triggers {
        cron('H */6 * * *')
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '15'))
        timeout(time: 20, unit: 'MINUTES')
    }

    environment {
        // Dossier du venv Python (cree a l'etape Install).
        VENV = 'venv'
    }

    stages {

        // 5.1 — Installation propre des dependances dans un venv.
        stage('Install') {
            steps {
                sh '''
                    python3 -m venv ${VENV}
                    . ${VENV}/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }

        // 5.2 — Scraping multi-sources -> data/jobs.csv
        stage('Scraping') {
            steps {
                sh '''
                    . ${VENV}/bin/activate
                    python scraper.py
                '''
            }
        }

        // 5.5 — Detection de changements (placee tot pour eviter le travail inutile = bonus).
        // Compare data/jobs.csv a data/jobs_previous.csv via SHA-256.
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
                        echo 'Changements detectes : poursuite du pipeline.'
                        // L'extraction courante devient la reference pour la prochaine fois.
                        sh 'cp data/jobs.csv data/jobs_previous.csv'
                    } else {
                        echo 'Aucune nouvelle offre : arret premature (build marque SUCCESS).'
                    }
                }
            }
        }

        // 5.3 — Transformation CSV -> public/index.html (seulement s'il y a du nouveau).
        stage('Conversion') {
            when { environment name: 'HAS_CHANGES', value: 'true' }
            steps {
                sh '''
                    . ${VENV}/bin/activate
                    python html_generator.py
                '''
            }
        }

        // 5.4 — Validation : >= 10 offres dans le CSV, et <table> + >= 10 lignes dans le HTML.
        stage('Tests') {
            when { environment name: 'HAS_CHANGES', value: 'true' }
            steps {
                sh '''
                    . ${VENV}/bin/activate
                    python - <<'PY'
import csv, re, sys

# 1) jobs.csv doit contenir au moins 10 offres (hors en-tete)
with open("data/jobs.csv", encoding="utf-8") as f:
    rows = list(csv.reader(f))
data_rows = max(len(rows) - 1, 0)
print(f"jobs.csv : {data_rows} lignes de donnees")
if data_rows < 10:
    print("ECHEC : moins de 10 offres dans jobs.csv")
    sys.exit(1)

# 2) index.html doit contenir une balise <table> et au moins 10 lignes <tr> de donnees
with open("public/index.html", encoding="utf-8") as f:
    html = f.read()
if "<table" not in html:
    print("ECHEC : aucune balise <table> dans index.html")
    sys.exit(1)
# Chaque ligne de donnees contient exactement un lien "Voir l'offre".
data_lines = len(re.findall(r"Voir l'offre", html))
print(f"index.html : {data_lines} lignes de donnees")
if data_lines < 10:
    print("ECHEC : moins de 10 lignes de donnees dans index.html")
    sys.exit(1)

print("Tests OK")
PY
                '''
            }
        }

        // 5.6 — Archivage des artefacts dans Jenkins.
        stage('Archive') {
            when { environment name: 'HAS_CHANGES', value: 'true' }
            steps {
                archiveArtifacts artifacts: 'data/jobs.csv, public/index.html, logs/log.txt',
                                 fingerprint: true, allowEmptyArchive: true
            }
        }

        // 5.7 — Deploiement public. Option retenue : publication HTML dans Jenkins
        // (visible dans le menu du job) + exemple GitHub Pages documente dans le README.
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
                // --- Option GitHub Pages (a activer avec un credential, voir README) ---
                // withCredentials([string(credentialsId: 'gh-token', variable: 'GH_TOKEN')]) {
                //     sh './deploy-ghpages.sh'
                // }
                echo 'Rapport publie. Voir "Offres d emploi" dans le menu du job.'
            }
        }
    }

    post {
        success { echo "Pipeline OK (changements: ${env.HAS_CHANGES})." }
        failure { echo 'Echec du pipeline : consultez les logs de l etape en rouge.' }
    }
}
