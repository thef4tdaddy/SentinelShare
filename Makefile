install:
	pip install -r requirements.txt
	cd frontend && npm install

dev:
	# Run backend and frontend (this is a simple example, ideally use two terminals)
	@echo "Please run 'uvicorn backend.main:app --reload' in one terminal"
	@echo "And 'cd frontend && npm run dev' in another"

build:
	cd frontend && npm run build

start:
	uvicorn backend.main:app

deploy:
	git push heroku main
