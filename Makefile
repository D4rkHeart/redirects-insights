build:
	docker-compose build

analyze:
	docker-compose run --rm analyzer

clean:
	rm -rf data/*
