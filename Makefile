.PHONY: setup start stop test lint format clean

# Install all dependencies
setup:
	python -m venv venv
	venv\Scripts\activate && pip install --upgrade pip
	venv\Scripts\activate && pip install -r requirements-dev.txt

# Start all services
start:
	bash infra/start_all.sh

# Stop Kafka and ZooKeeper (Redis is a service, manage via Windows)
stop:
	taskkill /F /FI "WINDOWTITLE eq Kafka*" 2>nul || true
	taskkill /F /FI "WINDOWTITLE eq ZooKeeper*" 2>nul || true
	@echo "Kafka and ZooKeeper stopped."

# Run all tests
test:
	venv\Scripts\activate && pytest tests/ -v

# Lint with ruff
lint:
	venv\Scripts\activate && ruff check .

# Format with black
format:
	venv\Scripts\activate && black .

# Clean compiled python files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	@echo "Cleaned."