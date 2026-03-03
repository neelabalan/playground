FROM golang:1.22-alpine AS builder

RUN apk add --no-cache gcc musl-dev sqlite-dev

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY . .

ENV CGO_ENABLED=1
RUN go build -o notes-api .

FROM alpine:3.20

RUN apk add --no-cache sqlite-libs

WORKDIR /app

COPY --from=builder /app/notes-api .

RUN mkdir -p /app/dbstore

EXPOSE 8080

CMD ["./notes-api"]
