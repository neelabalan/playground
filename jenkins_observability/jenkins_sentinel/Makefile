.PHONY: build clean test

build:
	mkdir -p build
	go build -o build/jenkins_sentinel .

clean:
	rm -rf build

test:
	go test ./...
