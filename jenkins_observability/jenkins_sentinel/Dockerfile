FROM golang:1.23 AS build
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
ARG TARGETOS=linux
ARG TARGETARCH=amd64
RUN CGO_ENABLED=0 GOOS=$TARGETOS GOARCH=$TARGETARCH go build -o /out/jenkins_sentinel ./cmd/daemon

FROM almalinux:9-minimal
RUN microdnf install -y ca-certificates shadow-utils && microdnf clean all
RUN useradd --system --create-home --home-dir /app --shell /sbin/nologin sentinel
WORKDIR /app
COPY --from=build /out/jenkins_sentinel /usr/local/bin/jenkins_sentinel
COPY config.json ./config.json
COPY sql ./sql
RUN chown -R sentinel:sentinel /app && chown sentinel:sentinel /usr/local/bin/jenkins_sentinel
USER sentinel
ENV CONFIG_PATH=/app/config.json
ENTRYPOINT ["jenkins_sentinel"]
