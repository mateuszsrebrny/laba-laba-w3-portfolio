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
    docker compose up -d "$@"
}

function stop_services() {
    echo "▶ Stopping all services..."
    docker compose down "$@"
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
  *)
    echo "Usage: $0 {tests|start|stop} [docker compose args]"
    exit 1
    ;;
esac


