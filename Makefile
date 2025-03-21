.PHONY: install run-all run-main run-database run-vector run-frontend

install:
	@echo "Installing Python dependencies..."
	cd Backend && \
	python3 -m venv venv && \
	source venv/bin/activate && \
	pip install -r requirements.txt
	@echo "Installing Node.js dependencies..."
	cd socratic-frontend && \
	npm install
	@echo "All dependencies installed successfully!"

# Individual service targets
run-main:
	cd Backend/main_service && \
	uvicorn app.main:app --reload --port 8000

run-database:
	cd Backend/database_service && \
	uvicorn app.main:app --reload --port 8001

run-vector:
	cd Backend/vector_service && \
	uvicorn app.main:app --reload --port 8002

run-frontend:
	cd socratic-frontend && \
	npm start

# To run all services, use separate terminal windows/tabs for each service
run-all:
	@echo "Please run each service in a separate terminal window:"
	@echo "- make run-main: Main service on port 8000"
	@echo "- make run-database: Database service on port 8001"
	@echo "- make run-vector: Vector service on port 8002"
	@echo "- make run-frontend: Frontend on port 3000"
	@echo ""
	@echo "Alternatively, you can start them all in separate terminals like this:"
	@echo "Terminal 1: cd $(PWD) && make run-main"
	@echo "Terminal 2: cd $(PWD) && make run-database"
	@echo "Terminal 3: cd $(PWD) && make run-vector"
	@echo "Terminal 4: cd $(PWD) && make run-frontend"