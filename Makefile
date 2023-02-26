SHELL 			:= /bin/bash
CMD 			:= python3
VENV 			:= test -d venv || python3 -m venv venv
ACTIVATE 		:= . venv/bin/activate
INSTALL  		:= pip install
IMAGE_NAME		:= webapp

# Check if the .env exists otherwise create it
ifeq (,$(wildcard .env))
$(shell touch .env)
endif

include .env

all:
	@echo "run server"
	@gunicorn --config  wsgi.py server:server
	@echo "Server stopped"


# Unit tests
test:
	@echo "Running tests..."
	@pytest  --verbose --cov=webapp
	@echo "Done."

coverage:
	@pytest --cov=webapp
	coverage report

help: ## Show this help
	@egrep -h '\s##\s' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:venv
	: # Activate venv and install smthing inside
	@echo "Installing..."
	@$(INSTALL) --upgrade pip
	@$(INSTALL) -r requirements.txt --no-cache-dir
	@$(INSTALL) -r requirements_dev.txt --no-cache-dir
	@echo "Done."

venv:
	#: # Create venv if it doesn't exist
	@echo "Creating venv..."
	@$(VENV)
	@echo "Done."

clean:
	@rm -rf venv
	@rm -rf dist build *.egg-info
	@find . -name "*.pyc" -exec rm {} \;
	@find . | grep -E '(__pycache__|\.pyc|\.pyo$$)' | xargs rm -rf


build:
	@echo "build image staging "
	echo ${GITHUB_TOKEN}
	@docker build -t ${ECR_REGISTRY}/${ECR_REPOSITORY}:${IMAGE_TAG}  . --build-arg GITHUB_TOKEN=${GITHUB_TOKEN} --build-arg USERNAME_REPO=${USERNAME_REPO} --build-arg EMAIL_REPO=${EMAIL_REPO}
	@docker tag ${ECR_REGISTRY}/${ECR_REPOSITORY}:${IMAGE_TAG} ${ECR_REGISTRY}/${ECR_REPOSITORY}:latest
	@docker push ${ECR_REGISTRY}/${ECR_REPOSITORY}:${IMAGE_TAG}
	@docker push ${ECR_REGISTRY}/${ECR_REPOSITORY}:latest
	@echo "deploy image $(IMAGE_NAME)"


lint: format ## Linter the code.
	@echo "🚨 Linting code"
	pre-commit run --all-files

re:  clean venv install

.PHONY: all test coverage help install venv clean build lint re
