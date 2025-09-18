.PHONY: build clean test generate run fmt tidy

build:
	mkdir -p build
	go build -o build/jenkins_sentinel .

run: build
	./build/jenkins_sentinel

clean:
	rm -rf build

test:
	go test ./...

generate:
	$(shell go env GOPATH)/bin/sqlc generate

fmt:
	go fmt ./...

tidy:
	go mod tidy
