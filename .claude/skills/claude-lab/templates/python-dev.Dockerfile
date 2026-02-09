# Claude Lab Python Dev Image
# Python development environment with k8s tools

FROM ubuntu:22.04

LABEL org.opencontainers.image.title="Claude Lab Python Dev"
LABEL org.opencontainers.image.description="Python development environment with Kubernetes tools"
LABEL claude-lab.template="python-dev"
LABEL claude-lab.version="1.0.0"

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC
ENV PYTHONUNBUFFERED=1

# Install system essentials
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    vim \
    nano \
    jq \
    yq \
    htop \
    tree \
    ca-certificates \
    build-essential \
    python3.11 \
    python3.11-dev \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Set python3.11 as default
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1 \
    && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

# Install kubectl
ARG KUBECTL_VERSION=v1.29.0
RUN curl -LO "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/amd64/kubectl" \
    && install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl \
    && rm kubectl

# Install helm
ARG HELM_VERSION=v3.14.0
RUN curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Install k9s
ARG K9S_VERSION=v0.31.0
RUN curl -sL "https://github.com/derailed/k9s/releases/download/${K9S_VERSION}/k9s_Linux_amd64.tar.gz" \
    | tar xvz -C /tmp \
    && mv /tmp/k9s /usr/local/bin/k9s \
    && chmod +x /usr/local/bin/k9s

# Install uv for Python package management
RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
    && ln -s /root/.cargo/bin/uv /usr/local/bin/uv

# Install common Python packages
RUN pip3 install --no-cache-dir --upgrade pip setuptools wheel \
    && pip3 install --no-cache-dir \
    kubernetes \
    pyyaml \
    requests \
    click \
    rich \
    pydantic \
    fastapi \
    uvicorn \
    pytest \
    pytest-cov \
    black \
    ruff \
    mypy \
    ipython \
    jupyter

# Shell enhancements
RUN echo 'alias k=kubectl' >> /root/.bashrc \
    && echo 'alias h=helm' >> /root/.bashrc \
    && echo 'source <(kubectl completion bash)' >> /root/.bashrc \
    && echo 'complete -F __start_kubectl k' >> /root/.bashrc

# Create common directories
RUN mkdir -p /workspace /data

WORKDIR /workspace

CMD ["/bin/bash"]
