# Claude Lab Base Image
# Essential tools for k3s development

FROM ubuntu:22.04

LABEL org.opencontainers.image.title="Claude Lab Base"
LABEL org.opencontainers.image.description="Base image for claude-lab environments with essential tools"
LABEL claude-lab.template="base"
LABEL claude-lab.version="1.0.0"

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Install system essentials
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    vim \
    nano \
    jq \
    htop \
    tree \
    ca-certificates \
    gnupg \
    lsb-release \
    software-properties-common \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install yq separately (not available in apt)
ARG YQ_VERSION=v4.40.5
RUN curl -sL "https://github.com/mikefarah/yq/releases/download/${YQ_VERSION}/yq_linux_arm64" -o /usr/local/bin/yq \
    && chmod +x /usr/local/bin/yq

# Install kubectl
ARG KUBECTL_VERSION=v1.29.0
RUN curl -LO "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/amd64/kubectl" \
    && install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl \
    && rm kubectl

# Install helm
ARG HELM_VERSION=v3.14.0
RUN curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Install k9s (Kubernetes CLI UI)
ARG K9S_VERSION=v0.31.0
RUN curl -sL "https://github.com/derailed/k9s/releases/download/${K9S_VERSION}/k9s_Linux_amd64.tar.gz" \
    | tar xvz -C /tmp \
    && mv /tmp/k9s /usr/local/bin/k9s \
    && chmod +x /usr/local/bin/k9s

# Install docker CLI (for docker-in-docker scenarios)
RUN curl -fsSL https://get.docker.com | sh

# Set up shell enhancements
RUN echo 'alias k=kubectl' >> /root/.bashrc \
    && echo 'alias h=helm' >> /root/.bashrc \
    && echo 'source <(kubectl completion bash)' >> /root/.bashrc \
    && echo 'complete -F __start_kubectl k' >> /root/.bashrc

# Create common directories
RUN mkdir -p /workspace /data

WORKDIR /workspace

# Default command
CMD ["/bin/bash"]
