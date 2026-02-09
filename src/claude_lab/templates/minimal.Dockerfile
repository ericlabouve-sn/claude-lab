# Claude Lab Minimal Image
# Lightweight image with just kubectl and helm

FROM ubuntu:22.04

LABEL org.opencontainers.image.title="Claude Lab Minimal"
LABEL org.opencontainers.image.description="Minimal image for claude-lab environments"
LABEL claude-lab.template="minimal"
LABEL claude-lab.version="1.0.0"

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Install only essentials
RUN apt-get update && apt-get install -y \
    curl \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install kubectl
ARG KUBECTL_VERSION=v1.29.0
RUN curl -LO "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/amd64/kubectl" \
    && install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl \
    && rm kubectl

# Install helm
ARG HELM_VERSION=v3.14.0
RUN curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

WORKDIR /workspace

CMD ["/bin/bash"]
