setup:
	pip3 install -r requirements.txt

validate: setup ## Validate the data package
	frictionless validate data/datapackage.json

web: setup  ## generate website
	python3 -m website.generator generate

collate: setup
	python3 -m versions.content collate

help:
	@echo 'Usage: make <command>'
	@echo
	@echo 'where <command> is one of the following:'
	@echo
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
