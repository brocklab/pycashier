FROM mambaorg/micromamba:0.24.0 as builder

COPY docker/builder.lock tmp/builder.lock

RUN micromamba \
  install --name base \
  --yes \
  -f tmp/builder.lock

ARG MAMBA_DOCKERFILE_ACTIVATE=1  # (otherwise python will not be found)

USER root

WORKDIR /pkg

COPY --chown=$MAMBA_USER:$MAMBA_USER . .

RUN pdm build --no-sdist --no-isolation

FROM mambaorg/micromamba:0.24.0 as prod

COPY docker/prod.lock tmp/prod.lock

RUN micromamba \
  install --name base \
  --yes \
  -f tmp/prod.lock \
  && \
  micromamba clean --all --force-pkgs-dirs --yes

ARG MAMBA_DOCKERFILE_ACTIVATE=1  # (otherwise python will not be found)

COPY --from=builder --chown=$MAMBA_USER:$MAMBA_USER /pkg/dist/ /pkg

RUN pip install /pkg/*

WORKDIR /data

ENTRYPOINT ["/usr/local/bin/_entrypoint.sh", "pycashier"]
