SETTINGS := postgres
WORF_SETTINGS_D := settings:tests/settings:tests/settings/$(SETTINGS)

# we add the virtualenv path to the PATH
export PATH := venv/bin:$(PATH)

.PHONY: format mypy wheels update release

all: format mypy test test-plugins

setup: virtualenv requirements

virtualenv:
	virtualenv --python python3 venv

requirements:
	# we install Worf itself
	pip install -e .

setup-plugins:
	# we install the plugins as well
	pip install -e ../worf-plugins/newsletter
	pip install -e ../worf-plugins/contact
test:
	WORF_SETTINGS_D=$(WORF_SETTINGS_D) pytest $(args) tests
	
test-plugins:
	WORF_SETTINGS_D=$(WORF_SETTINGS_D) pytest $(args) worf/plugins

format:
	black worf/
	black tests/

mypy:
	mypy worf/
	mypy tests/

wheels:
	pip wheel --wheel-dir wheels -r requirements.txt


update:
	pip3 install pur
	pur -r requirements.txt

release:
	python3 setup.py sdist
	twine upload --skip-existing dist/* -u ${TWINE_USER} -p ${TWINE_PASSWORD}
