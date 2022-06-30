FROM mambaorg/micromamba:0.24.0 as builder

RUN micromamba \
  install --name base \
  --yes \
  -c conda-forge \
  python=3.9 \
  git \
  pdm \
  pdm-pep517 && \
  micromamba clean --all --force-pkgs-dirs --yes

ARG MAMBA_DOCKERFILE_ACTIVATE=1  # (otherwise python will not be found)

USER root

WORKDIR /pkg

COPY --chown=$MAMBA_USER:$MAMBA_USER . .

RUN pdm build --no-sdist --no-isolation

FROM mambaorg/micromamba:0.24.0 as prod

RUN micromamba \
  install --name base \
  --yes \
  -c conda-forge \
  -c bioconda \
  python=3.9 \
  cutadapt>=3.5 \
  starcode>=1.4 \
  pysam=0.17* \
  fastp=0.23* \
  rich>=10 \
  click-rich-help>=22.1 \
  click>=8.1.0 \
  tomlkit>=0.10 \
  && \
  micromamba clean --all --force-pkgs-dirs --yes

ARG MAMBA_DOCKERFILE_ACTIVATE=1  # (otherwise python will not be found)

COPY --from=builder --chown=$MAMBA_USER:$MAMBA_USER /pkg/dist/ /pkg

RUN pip install /pkg/*

WORKDIR /data

ENTRYPOINT ["/usr/local/bin/_entrypoint.sh", "pycashier"]
