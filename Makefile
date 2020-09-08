.DEFAULT_GOAL := default

default:
	docker build -t hernrup/hass_ae:$$(git rev-parse --short HEAD) -t hernrup/hass_ae:latest .