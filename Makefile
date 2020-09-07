.DEFAULT_GOAL := default

default:
	docker build -t hernrup/hass_ae:$(git rev-parse --short HEAD) .
	docker tag hernrup/hass_ae:$(git rev-parse --short HEAD) hernrup/hass_ae:latest  .