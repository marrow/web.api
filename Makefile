PROJECT = web.api
USE = development
PIP_CACHE_DIR = ${VIRTUAL_ENV}/lib/pip-cache

.SILENT:
.PHONY: all develop clean veryclean test


all: develop test


help:  ## Show this help message and exit.
	@echo "Usage: make <command>\n\033[36m\033[0m"
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*?##/ { printf "\033[36m%-18s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST) | sort


depend: ${PROJECT}.egg-info/PKG-INFO  ## Ensure package dependencies are declared.
	cp ${PROJECT}.egg-info/requires.txt .packaging/depend


develop: ${PROJECT}.egg-info/PKG-INFO  ## Ensure the project is installed for development.
	@echo " \033[1;32m*\033[0m Installing \033[1m${PROJECT}\033[0m and \033[1;33m$(USE)\033[0m dependencies..."
	
	mkdir -p ${VIRTUAL_ENV}/lib/pip-cache .packaging
	pip install -q --compile -Ue ".[${USE}]"


clean:  ## Clean out cached Python bytecode.
	@echo " \033[1;33m*\033[0m Cleaning \033[1m${PROJECT}\033[0m bytecode..."
	
	find . -name __pycache__ -exec rm -rf {} +


veryclean: clean  ## Clean bytecode and package metadata.
	@echo " \033[1;33m*\033[0m Cleaning \033[1m${PROJECT}\033[0m metadata..."
	
	rm -rf *.egg-info
	rm -rf .packaging/*


test:  ## Execute the entire test suite.
	@echo " \033[1;34m*\033[0m Testing \033[1m${PROJECT}\033[0m..."
	pytest -W ignore::DeprecationWarning:uri.bucket: -W ignore::DeprecationWarning:uri.qso:


testloop:  ## Automatically execute the test suite limited to one failure.
	find web test -name \*.py | entr -c \
		pytest --ff --maxfail=1 \
		-W ignore::DeprecationWarning:uri.bucket: -W ignore::DeprecationWarning:uri.qso:


${PROJECT}.egg-info/PKG-INFO: setup.py setup.cfg
	@echo " \033[1;32m*\033[0m Collecting \033[1m${PROJECT}\033[0m metadata..."
	
	./setup.py -q egg_info
