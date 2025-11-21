FROM mcr.microsoft.com/devcontainers/base:jammy

ARG PIXI_VERSION=v0.55.0

RUN curl -L -o /usr/local/bin/pixi -fsSL --compressed "https://github.com/prefix-dev/pixi/releases/download/${PIXI_VERSION}/pixi-$(uname -m)-unknown-linux-musl" \
    && chmod +x /usr/local/bin/pixi \
    && pixi info

# set some user and workdir settings to work nicely with vscode
ENV VSCODE_HOME=/home/vscode \
    VSCODE_USER=vscode \
    SHELL=/bin/bash
USER ${VSCODE_USER}
WORKDIR ${VSCODE_HOME}

RUN echo 'eval "$(pixi completion -s bash)"' >> ${VSCODE_HOME}/.bashrc
