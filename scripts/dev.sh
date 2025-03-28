#!/bin/bash
set -e

APP_IMAGE_NAME="laba-laba-app"
TEST_IMAGE_NAME="laba-laba-tests"

function build_app() {
    echo "▶ Building app image..."
    docker compose build laba-laba-app
}

function build_tests() {
    echo "▶ Building test image..."
    docker build -f Dockerfile.tests -t "$TEST_IMAGE_NAME" .
}

function run_tests() {
    build_app
    build_tests
    echo "▶ Running tests..."
    docker run --rm --tty "$TEST_IMAGE_NAME"
}

function start_services() {
    echo "▶ Starting app and database..."
    GIT_COMMIT=$(git rev-parse HEAD) docker compose up -d "$@"
}

function stop_services() {
    echo "▶ Stopping all services..."
    docker compose down "$@"
}

function query_db() {
    echo "▶ Querying database ... "
    echo "$@" | mysql -ull_dev_user -pll_dev_db_pass -h127.0.0.1 ll_dev
}

function exec_app() {    
    echo "▶ Executing command ... "
    docker exec -it laba-laba-dev-app "$@"
}

CMD="$1"
shift || true

case "$CMD" in
  tests)
    run_tests
    ;;
  start)
    run_tests
    echo "✅ Tests passed. Starting app and database..."
    start_services "$@"
    ;;
  stop)
    stop_services "$@"
    ;;
  restart)
    stop_services "$@"
    echo "♻️ Restarting app and database..."
    run_tests
    echo "✅ Tests passed. Starting app and database..."
    start_services
    ;;
  query)
    query_db "$@"
    ;;
  exec)
    exec_app "$@"
    ;;
  *)
    echo "Usage: $0 {tests|start|stop} [docker compose args]"
    exit 1
    ;;
esac

