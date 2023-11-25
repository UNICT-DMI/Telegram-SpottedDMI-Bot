# Run all the tests and linters in the CI pipeline locally
pytest tests || (echo "Tests failed" && exit 1)
pylint src tests || (echo "Pylint failed" && exit 1)
black --check src tests || (echo "Black failed" && exit 1)
isort --check-only src tests || (echo "Isort failed" && exit 1)
