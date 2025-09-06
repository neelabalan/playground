.PHONY: build clean test generate

build:
	mkdir -p build
	go build -o build/jenkins_sentinel .

clean:
	rm -rf build

test:
	go test ./...

generate:
	$(shell go env GOPATH)/bin/sqlc generate
