#!/bin/bash
set -e

APP_IMAGE_NAME="laba-laba-app"
TEST_IMAGE_NAME="laba-laba-tests"

function build_app() {
    echo "▶ Building app image..."
    env UID=$(id -u) GID=$(id -g) docker compose build laba-laba-app
}

function build_tests() {
    echo "▶ Building test image..."
    docker build -f Dockerfile.tests -t "$TEST_IMAGE_NAME" .
}

function build_images() {
    build_app
    build_tests
}

function run_on_test_image() {
    if [ "$#" -eq 0 ]; then
        echo "▶ Running tests..."
    else
        echo "▶ Running $@..."
    fi

    docker run --rm --tty \
        -v "$(pwd)/tests:/src/tests" \
        -v "$(pwd)/app:/src/app" \
        -v "$(pwd)/alembic:/src/alembic" \
        "$TEST_IMAGE_NAME" "$@"
}

function run_tests() {
    run_on_test_image $@
}

function run_format() {
    run_on_test_image black app tests alembic
}

function run_lint() {
    run_on_test_image ruff check app tests alembic
}

function run_lint_fix() {
    run_on_test_image ruff check --fix app tests alembic
}

function run_isort() {
    run_on_test_image isort --profile black app tests alembic
}

function start_services() {
    echo "▶ Starting app and database..."
    env GIT_COMMIT=$(git rev-parse HEAD) UID=$(id -u) GID=$(id -g) docker compose up -d "$@"
}

function stop_services() {
    echo "▶ Stopping all services..."
    env UID=$(id -u) GID=$(id -g) docker compose down "$@"
}

function query_db() {
    echo "▶ Querying database ... "
    echo "$@" | mysql -ull_dev_user -pll_dev_db_pass -h127.0.0.1 ll_dev
}

function exec_app() {
    echo "▶ Executing command ... "
    docker exec -it laba-laba-dev-app "$@"
}

function install_githooks() {
    
	ln -sf "$(pwd)/.githooks/pre-commit" "$(pwd)/.git/hooks/pre-commit"
	chmod +x "$(pwd)/.git/hooks/pre-commit"

	echo "Git hooks installed successfully!"
}

function docker_prune() {
    docker image prune -f
}

CMD="$1"
shift || true

case "$CMD" in
  build)
    build_images
    ;;
  tests)
    run_tests "$@"
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
    build_images
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
  format)
    run_format
    ;;
  lint)
    run_lint
    ;;
  isort)
    run_isort
    ;;
  lint_fix)
    run_lint_fix
    ;;
  code_fix)
    build_images
    run_isort
    run_format
    run_lint_fix
    ;;
  install_githooks)
    install_githooks
    ;;
  docker_prune)
    docker_prune
    ;;
  *)
    echo "Usage: $0 COMMAND [optional PARAMS]"
    exit 1
    ;;
esac


