.PHONY: images

images:
	cd docker && docker build -t phpcs -f phpcs.Dockerfile .
	cd docker && docker build -t nodejs -f nodejs.Dockerfile .
	cd docker && docker build -t python2 -f python2.Dockerfile .
	cd docker && docker build -t ruby2 -f ruby2.Dockerfile .
	cd docker && docker build -t luacheck -f luacheck.Dockerfile .
	cd docker && docker build -t golint -f golint.Dockerfile .
	cd docker && docker build -t checkstyle -f checkstyle.Dockerfile .
	cd docker && docker build -t shellcheck -f shellcheck.Dockerfile .
	cd docker && docker build -t gpg -f gpg.Dockerfile .
