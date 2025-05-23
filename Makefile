# Start containers
up:
	docker-compose up --build -d

# Stop containers
down:
	docker-compose down

# Rebuild containers
rebuild:
	docker-compose down
	docker-compose up --build -d

# View logs
logs:
	docker-compose logs -f

# Restart services
restart:
	docker-compose restart

# Shell into FastAPI container (replace 'web' with your actual service name if different)
shell:
	docker-compose exec feedbackapp /bin/sh

# Shell into Postgres
psql:
	docker-compose exec postgresdb psql -U $$POSTGRES_USER -d $$POSTGRES_DB

# Clean all volumes (use with caution!)
clean:
	docker-compose down -v

# Run tests
test:
	pytest tests/ --disable-warnings -v