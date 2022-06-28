FROM mambaorg/micromamba:0.22.0

USER root
RUN mkdir /code && chown -R $MAMBA_USER:$MAMBA_USER /code
USER $MAMBA_USER

RUN micromamba \
  install --name base \
  --yes \
  -c conda-forge \
  -c bioconda \
  git \
  python>=3.7 \
  cutadapt>=3.5 \
  starcode>=1.4 \
  pysam=0.17* \
  fastp=0.23* \
  rich>=10 \
  click-rich-help>=22.1 \
  click>=8.1.0 \
  tomlkit>=0.10 \
  && \
  micromamba clean --all --yes

ARG MAMBA_DOCKERFILE_ACTIVATE=1  # (otherwise python will not be found)

WORKDIR /code

# install dependencies and project
COPY --chown=$MAMBA_USER:$MAMBA_USER . ./

RUN pip install --no-deps .

WORKDIR /data

ENTRYPOINT ["/usr/local/bin/_entrypoint.sh", "pycashier"]
