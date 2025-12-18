FROM almalinux:9

ARG VSCODE_SERVER_VERSION=latest

RUN dnf install -y --allowerasing \
    curl \
    tar \
    gzip \
    && dnf clean all

# install VS Code Server
RUN mkdir -p /root/.vscode-server/bin && \
    if [ "$VSCODE_SERVER_VERSION" = "latest" ]; then \
        echo "fetching latest VS Code Server version..." && \
        VSCODE_SERVER_VERSION=$(curl -s https://update.code.visualstudio.com/api/releases/stable | head -n 1); \
    fi && \
    echo "installing VS Code Server version: $VSCODE_SERVER_VERSION" && \
    curl -sSL "https://update.code.visualstudio.com/commit:${VSCODE_SERVER_VERSION}/server-linux-x64/stable" -o /tmp/vscode-server.tar.gz && \
    tar -xzf /tmp/vscode-server.tar.gz -C /root/.vscode-server/bin/ && \
    mv /root/.vscode-server/bin/vscode-server-linux-x64 /root/.vscode-server/bin/${VSCODE_SERVER_VERSION} && \
    rm /tmp/vscode-server.tar.gz && \
    ls -la /root/.vscode-server/bin/ && echo "vscode server installed successfully"

# install extensions
COPY extensions.txt /tmp/
COPY install_extensions.sh /tmp/
RUN chmod +x /tmp/install_extensions.sh && \
    /tmp/install_extensions.sh /tmp/extensions.txt && \
    rm /tmp/install_extensions.sh /tmp/extensions.txt

CMD ["/bin/bash"]
