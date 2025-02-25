# Define ports
FRONTEND_PORT = 3000
BACKEND_PORT = 8000
LLM_PORT = 8001

# Define paths
FRONTEND_DIR = ./socratic-frontend
BACKEND_DIR = ./Backend/App
MICROSERVICE_DIR = ./Backend/llm_service

.PHONY: servers stop clean logs

# Create logs directory
logs:
    @mkdir -p logs

# Start all servers
servers: logs
    @echo "Starting all servers..."
    @echo "Frontend: http://localhost:$(FRONTEND_PORT)"
    @echo "Backend: http://localhost:$(BACKEND_PORT)"
    @echo "LLM Service: http://localhost:$(LLM_PORT)"
    @(cd $(FRONTEND_DIR) && PORT=$(FRONTEND_PORT) npm start > ../logs/frontend.log 2>&1 & echo "Frontend started on port $(FRONTEND_PORT)")
    @(cd $(BACKEND_DIR) && uvicorn app.main:app --reload --port $(BACKEND_PORT) > ../../logs/backend.log 2>&1 & echo "Backend started on port $(BACKEND_PORT)")
    @(cd $(MICROSERVICE_DIR) && uvicorn app.main:app --reload --port $(LLM_PORT) > ../../logs/microservice.log 2>&1 & echo "LLM service started on port $(LLM_PORT)")
    @echo "All servers are starting. Check logs directory for details."
    @echo "API docs available at:"
    @echo "- Backend: http://localhost:$(BACKEND_PORT)/docs"
    @echo "- LLM Service: http://localhost:$(LLM_PORT)/docs"

# Stop all servers
stop:
    @echo "Stopping all servers..."
    @pkill -f "npm start" || true
    @pkill -f "uvicorn" || true
    @echo "All servers stopped"

# Clean up log files
clean:
    @rm -rf logs/
    @echo "Cleaned up log files"

# Watch logs in real-time
watch-logs:
    @tail -f logs/*.log