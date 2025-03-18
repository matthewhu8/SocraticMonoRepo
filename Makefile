.PHONY: install

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
