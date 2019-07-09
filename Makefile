.PHONY: images

images:
	cd docker && docker build -t php -f php.Dockerfile .
	cd docker && docker build -t nodejs -f nodejs.Dockerfile .
	cd docker && docker build -t python2 -f python2.Dockerfile .
	cd docker && docker build -t python3 -f python3.Dockerfile .
	cd docker && docker build -t ruby2 -f ruby2.Dockerfile .
	cd docker && docker build -t luacheck -f luacheck.Dockerfile .
	cd docker && docker build -t golint -f golint.Dockerfile .
	cd docker && docker build -t checkstyle -f checkstyle.Dockerfile .
	cd docker && docker build -t shellcheck -f shellcheck.Dockerfile .
	cd docker && docker build -t gpg -f gpg.Dockerfile .
	cd docker && docker build -t credo -f credo.Dockerfile .
	cd docker && docker build -t eslint -f eslint.Dockerfile .
	cd docker && docker build -t ktlint -f ktlint.Dockerfile .


# Utility target for checking required parameters
guard-%:
	@if [ "$($*)" = '' ]; then \
		echo "Missing required $* variable."; \
		exit 1; \
	fi;

tag: guard-VERSION
	sed -i'' -e "s/__version__ = '\(.*\)'/__version__ = '$(VERSION)'/" lintreview/__init__.py
	git add lintreview/__init__.py
	git commit -m 'Bump version'
	git tag -s $(VERSION)
	git push origin
	git push origin --tags
	python setup.py bdist_wheel --universal upload
	python setup.py sdist upload

release: tag
