.PHONY: images

images:
	cd docker && docker build -t phpcs -f phpcs.Dockerfile .
	cd docker && docker build -t nodejs -f nodejs.Dockerfile .
	cd docker && docker build -t python2 -f python2.Dockerfile .
