FROM python:3.9.13-slim-bullseye as builder

RUN apt-get update \
  && apt-get install \
    -y \
    --no-install-recommends \
    git \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

RUN python -m \
    pip install \
    --user \
    --no-warn-script-location \
    build

WORKDIR /pkg

COPY . .

# ignore files that weren't copied over so the git status isn't dirty
RUN git ls-files --deleted | git update-index --assume-unchanged --stdin

RUN python -m \
  build \
  --wheel \
  --outdir dist/

FROM mambaorg/micromamba:0.24.0 as prod

COPY docker/prod.lock tmp/prod.lock

RUN micromamba \
  install --name base \
  --yes \
  -f tmp/prod.lock \
  && \
  micromamba clean --all --force-pkgs-dirs --yes

RUN find -name '*.a' -delete && \
  rm -rf /opt/conda/conda-meta && \
  rm -rf /opt/conda/include && \
  rm /opt/conda/lib/libpython3.9.so.1.0 && \
  find -name '__pycache__' -type d -exec rm -rf '{}' '+' && \
  rm -rf /opt/conda/lib/python3.9/idlelib /opt/conda/lib/python3.9/ensurepip \
    /opt/conda/lib/libasan.so.5.0.0 \
    /opt/conda/lib/libtsan.so.0.0.0 \
    /opt/conda/lib/liblsan.so.0.0.0 \
    /opt/conda/lib/libubsan.so.1.0.0 \
    /opt/conda/bin/x86_64-conda-linux-gnu-ld \
    /opt/conda/bin/sqlite3 \
    /opt/conda/bin/openssl \
    /opt/conda/share/terminfo && \
  find /opt/conda/lib/python3.9/site-packages/ -name 'tests' -type d -exec rm -rf '{}' '+' && \
  find /opt/conda/lib/python3.9/site-packages -name '*.pyx' -delete && \
  rm -rf /opt/conda/lib/python3.9/site-packages/uvloop/loop.c

ARG MAMBA_DOCKERFILE_ACTIVATE=1  # (otherwise python will not be found)

COPY --from=builder --chown=$MAMBA_USER:$MAMBA_USER /pkg/dist/ /pkg

RUN pip install /pkg/*

WORKDIR /data

# ENTRYPOINT ["/usr/local/bin/_entrypoint.sh", "pycashier"]
