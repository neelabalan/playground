.PHONY: build build-daemon build-mcp clean test generate run run-daemon fmt tidy

build: build-daemon build-mcp

build-daemon:
	mkdir -p build
	go build -o build/daemon ./cmd/daemon

build-mcp:
	mkdir -p build
	go build -o build/mcpserver ./cmd/mcp

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
