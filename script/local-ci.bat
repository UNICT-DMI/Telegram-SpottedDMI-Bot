@echo off
rem Run all the tests and linters in the CI pipeline locally
pytest tests
pylint src tests
black --check src tests
isort --check-only src tests
