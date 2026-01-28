.PHONY: up down logs restart build shell

up:
	docker compose up -d

build:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f

restart:
	docker compose restart
	docker compose logs -f

shell:
	docker compose exec app bash
