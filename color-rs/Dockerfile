FROM rust:1.85.1-slim-bookworm as builder
WORKDIR /color-rs
COPY . /color-rs
RUN cargo build --release 
FROM almalinux:9.5-minimal
COPY --from=builder /color-rs/target/release/color-rs /usr/local/bin/color-rs


ENTRYPOINT [ "/usr/local/bin/color-rs" ]