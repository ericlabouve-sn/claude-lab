# Claude Lab K8s Full Image
# Comprehensive Kubernetes development environment

FROM ubuntu:22.04

LABEL org.opencontainers.image.title="Claude Lab K8s Full"
LABEL org.opencontainers.image.description="Full-featured Kubernetes development environment"
LABEL claude-lab.template="k8s-full"
LABEL claude-lab.version="1.0.0"

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
    python3 \
    python3-pip \
    unzip \
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

# Install k9s
ARG K9S_VERSION=v0.31.0
RUN curl -sL "https://github.com/derailed/k9s/releases/download/${K9S_VERSION}/k9s_Linux_amd64.tar.gz" \
    | tar xvz -C /tmp \
    && mv /tmp/k9s /usr/local/bin/k9s \
    && chmod +x /usr/local/bin/k9s

# Install kubectx and kubens
RUN git clone https://github.com/ahmetb/kubectx /opt/kubectx \
    && ln -s /opt/kubectx/kubectx /usr/local/bin/kubectx \
    && ln -s /opt/kubectx/kubens /usr/local/bin/kubens

# Install kustomize
ARG KUSTOMIZE_VERSION=v5.3.0
RUN curl -sL "https://github.com/kubernetes-sigs/kustomize/releases/download/kustomize/${KUSTOMIZE_VERSION}/kustomize_${KUSTOMIZE_VERSION}_linux_amd64.tar.gz" \
    | tar xvz -C /tmp \
    && mv /tmp/kustomize /usr/local/bin/kustomize \
    && chmod +x /usr/local/bin/kustomize

# Install stern (multi-pod log tailing)
ARG STERN_VERSION=1.28.0
RUN curl -sL "https://github.com/stern/stern/releases/download/v${STERN_VERSION}/stern_${STERN_VERSION}_linux_amd64.tar.gz" \
    | tar xvz -C /tmp \
    && mv /tmp/stern /usr/local/bin/stern \
    && chmod +x /usr/local/bin/stern

# Install flux CLI
RUN curl -s https://fluxcd.io/install.sh | bash

# Install ArgoCD CLI
ARG ARGOCD_VERSION=v2.10.0
RUN curl -sSL -o /usr/local/bin/argocd "https://github.com/argoproj/argo-cd/releases/download/${ARGOCD_VERSION}/argocd-linux-amd64" \
    && chmod +x /usr/local/bin/argocd

# Install Istio CLI
ARG ISTIO_VERSION=1.20.0
RUN curl -L https://istio.io/downloadIstio | ISTIO_VERSION=${ISTIO_VERSION} sh - \
    && mv istio-${ISTIO_VERSION}/bin/istioctl /usr/local/bin/ \
    && rm -rf istio-${ISTIO_VERSION}

# Install docker CLI
RUN curl -fsSL https://get.docker.com | sh

# Install Terraform
ARG TERRAFORM_VERSION=1.7.0
RUN curl -sL "https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip" -o /tmp/terraform.zip \
    && unzip /tmp/terraform.zip -d /usr/local/bin \
    && rm /tmp/terraform.zip

# Install useful Python packages
RUN pip3 install --no-cache-dir \
    kubernetes \
    pyyaml \
    requests \
    click \
    rich

# Shell enhancements
RUN echo 'alias k=kubectl' >> /root/.bashrc \
    && echo 'alias h=helm' >> /root/.bashrc \
    && echo 'alias kx=kubectx' >> /root/.bashrc \
    && echo 'alias kns=kubens' >> /root/.bashrc \
    && echo 'source <(kubectl completion bash)' >> /root/.bashrc \
    && echo 'complete -F __start_kubectl k' >> /root/.bashrc \
    && echo 'source <(helm completion bash)' >> /root/.bashrc

# Create common directories
RUN mkdir -p /workspace /data /charts /manifests

WORKDIR /workspace

CMD ["/bin/bash"]
