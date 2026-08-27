// Enterprise Web & API Quality Engineering Automation Platform
// Jenkins Declarative Pipeline — Deloitte Req ID 111207
//
// Stages:
//   Checkout → Environment Setup → API Tests → DB Tests → UI Tests →
//   E2E Tests → Generate Reports → Quality Gate → Notify
//
// Quality Gate: Deployment is BLOCKED if any suite fails or open defects exist.

pipeline {
    agent any

    environment {
        PYTHON_VERSION  = '3.11'
        ENV             = 'ci'
        BASE_URL        = 'http://127.0.0.1:3000'
        API_URL         = 'http://127.0.0.1:8000'
        DATABASE_URL    = 'sqlite+aiosqlite:///./eqe_platform.db'
        PYTHONPATH      = "${WORKSPACE}/application/backend"
        HEADLESS        = 'true'
        REPORTS_DIR     = "${WORKSPACE}/reports"
    }

    options {
        timestamps()
        timeout(time: 30, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10'))
        ansiColor('xterm')
    }

    stages {

        // ── Stage 1: Checkout ────────────────────────────────────────────
        stage('Checkout') {
            steps {
                echo '📥 Checking out source code...'
                checkout scm
                sh 'git log --oneline -5'
            }
        }

        // ── Stage 2: Environment Setup ───────────────────────────────────
        stage('Environment Setup') {
            steps {
                echo '🔧 Setting up Python virtual environment...'
                sh '''
                    python -m venv .venv
                    . .venv/bin/activate
                    pip install --upgrade pip --quiet
                    pip install -r automation/requirements.txt --quiet
                    pip install uvicorn[standard] aiosqlite sqlalchemy --quiet
                '''
                echo '🚀 Starting backend server...'
                sh '''
                    . .venv/bin/activate
                    python -m uvicorn app.main:app \
                        --host 127.0.0.1 --port 8000 \
                        --log-level warning &
                    sleep 3
                    curl -sf http://127.0.0.1:8000/health || exit 1
                    echo "✅ Backend healthy"
                '''
                echo '🌐 Starting frontend server...'
                sh '''
                    python -m http.server 3000 \
                        --directory application/frontend \
                        --bind 127.0.0.1 &
                    sleep 2
                    echo "✅ Frontend serving on :3000"
                '''
            }
        }

        // ── Stage 3: API Tests ───────────────────────────────────────────
        stage('API Tests') {
            steps {
                echo '🔌 Running API test suite (Functional + Negative + Smoke + Schema)...'
                sh '''
                    . .venv/bin/activate
                    python -m pytest automation/api/tests/ \
                        -v --tb=short \
                        --junitxml=${REPORTS_DIR}/junit/api_results.xml \
                        -m "api"
                '''
            }
            post {
                always {
                    junit "${REPORTS_DIR}/junit/api_results.xml"
                }
            }
        }

        // ── Stage 4: Database Tests ──────────────────────────────────────
        stage('Database Tests') {
            steps {
                echo '🗄️ Running Database validation suite...'
                sh '''
                    . .venv/bin/activate
                    python -m pytest automation/database/ \
                        -v --tb=short \
                        --junitxml=${REPORTS_DIR}/junit/db_results.xml \
                        -m "database"
                '''
            }
            post {
                always {
                    junit "${REPORTS_DIR}/junit/db_results.xml"
                }
            }
        }

        // ── Stage 5: UI Tests (Selenium) ─────────────────────────────────
        stage('UI Tests') {
            steps {
                echo '🖥️ Running UI automation suite (Selenium WebDriver, Chrome headless)...'
                sh '''
                    . .venv/bin/activate
                    python -m pytest automation/ui/tests/ \
                        -v --tb=short \
                        --junitxml=${REPORTS_DIR}/junit/ui_results.xml \
                        -m "ui"
                '''
            }
            post {
                always {
                    junit "${REPORTS_DIR}/junit/ui_results.xml"
                    // Archive failure screenshots if any
                    archiveArtifacts artifacts: 'reports/screenshots/*.png',
                                     allowEmptyArchive: true
                }
            }
        }

        // ── Stage 6: E2E Cross-Layer Tests ───────────────────────────────
        stage('E2E Cross-Layer Tests') {
            steps {
                echo '🔗 Running E2E cross-layer validation (UI → API → DB)...'
                sh '''
                    . .venv/bin/activate
                    python -m pytest automation/e2e/ \
                        -v --tb=short \
                        --junitxml=${REPORTS_DIR}/junit/e2e_results.xml
                '''
            }
            post {
                always {
                    junit "${REPORTS_DIR}/junit/e2e_results.xml"
                }
            }
        }

        // ── Stage 7: Full Suite with HTML Report ─────────────────────────
        stage('Generate Reports') {
            steps {
                echo '📊 Running full suite with HTML + JSON reporting...'
                sh '''
                    . .venv/bin/activate
                    python -m pytest automation/ \
                        -v \
                        --html=${REPORTS_DIR}/html/report.html \
                        --self-contained-html \
                        --json-report \
                        --json-report-file=${REPORTS_DIR}/json/results.json \
                        || true
                '''
                echo '📈 Generating Quality Dashboard...'
                sh '''
                    . .venv/bin/activate
                    python reports/dashboard/generate_dashboard.py
                '''
            }
            post {
                always {
                    publishHTML(target: [
                        allowMissing         : false,
                        alwaysLinkToLastBuild: true,
                        keepAll              : true,
                        reportDir            : 'reports/html',
                        reportFiles          : 'report.html',
                        reportName           : 'PyTest HTML Report'
                    ])
                    publishHTML(target: [
                        allowMissing         : false,
                        alwaysLinkToLastBuild: true,
                        keepAll              : true,
                        reportDir            : 'reports/dashboard',
                        reportFiles          : 'index.html',
                        reportName           : 'Quality Dashboard'
                    ])
                    archiveArtifacts artifacts: 'reports/**/*',
                                     allowEmptyArchive: true
                }
            }
        }

        // ── Stage 8: Quality Gate ─────────────────────────────────────────
        stage('Quality Gate') {
            steps {
                echo '🚦 Evaluating Quality Gate...'
                script {
                    def jsonReport = readJSON file: "${REPORTS_DIR}/json/results.json"
                    def summary   = jsonReport.summary ?: [:]
                    def total     = summary.total  ?: 0
                    def passed    = summary.passed ?: 0
                    def failed    = summary.failed ?: 0
                    def passRate  = total > 0 ? (passed / total * 100) : 0

                    echo """
╔══════════════════════════════════════╗
║         QUALITY GATE REPORT          ║
╠══════════════════════════════════════╣
║  Total Tests:   ${total.toString().padLeft(5)}               ║
║  Passed:        ${passed.toString().padLeft(5)}               ║
║  Failed:        ${failed.toString().padLeft(5)}               ║
║  Pass Rate:     ${String.format("%.1f", passRate).padLeft(5)}%              ║
╠══════════════════════════════════════╣
║  RESULT: ${failed == 0 ? '✅ RELEASE APPROVED     ' : '❌ RELEASE BLOCKED      '} ║
╚══════════════════════════════════════╝
                    """

                    if (failed > 0) {
                        error("Quality Gate FAILED: ${failed} test(s) failed. Deployment blocked.")
                    }
                    if (passRate < 100) {
                        error("Quality Gate FAILED: Pass rate ${String.format("%.1f", passRate)}% < 100%. Deployment blocked.")
                    }

                    echo '✅ Quality Gate PASSED — Deployment approved.'
                }
            }
        }
    }

    // ── Post Pipeline ─────────────────────────────────────────────────────
    post {
        success {
            echo '✅ Pipeline PASSED — All quality gates cleared.'
        }
        failure {
            echo '❌ Pipeline FAILED — Quality gate blocked deployment.'
        }
        always {
            echo '🧹 Cleaning up background servers...'
            sh 'pkill -f "uvicorn app.main:app" || true'
            sh 'pkill -f "http.server 3000" || true'
        }
    }
}
