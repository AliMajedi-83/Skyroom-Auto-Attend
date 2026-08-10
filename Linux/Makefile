.PHONY: setup run clean install-driver
setup:
	@echo "1. Installing system dependencies (requires sudo)..."
	sudo apt update && sudo apt install -y ffmpeg pulseaudio python3-pip python3-tk python3-venv libportaudio2
	
	@echo "2. Creating virtual environment and installing python packages..."
	python3 -m venv venv
	./venv/bin/pip install --upgrade pip
	./venv/bin/pip install -r requirements.txt
	
	@echo "3. Downloading and setting up Firefox driver..."
	wget -q https://github.com/mozilla/geckodriver/releases/download/v0.34.0/geckodriver-v0.34.0-linux64.tar.gz
	tar -xvzf geckodriver-v0.34.0-linux64.tar.gz
	chmod +x geckodriver
	rm geckodriver-v0.34.0-linux64.tar.gz
	
	@echo "✅ Everything is set up successfully!"

run:
	@echo "Starting the Skyroom Bot..."
	./venv/bin/python3 main.py

clean:
	@echo "Cleaning up project files..."
	rm -rf __pycache__/
	rm -f classes.db
	rm -f *.mp3 *.mp4
	rm -f geckodriver
	rm -rf venv
	@echo "Clean up complete!"
