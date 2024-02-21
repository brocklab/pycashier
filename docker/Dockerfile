# FROM python:3.10.9-slim-bullseye as builder
FROM python@sha256:6862d8ed663a47f649ba5aababed01e44741a032e80d5800db619f5113f65434 as builder

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
RUN bash -o pipefail -c 'git ls-files --deleted | git update-index --assume-unchanged --stdin'

RUN python -m \
  build \
  --wheel \
  --outdir dist/

# FROM mambaorg/micromamba:git-4427b19-bullseye as prod
FROM mambaorg/micromamba@sha256:e0bf91ac1ef7cedd7c8b9347d4041cd61049b0016fea41ac4c19d4917145c9c2 as prod

COPY --chown=$MAMBA_USER:$MAMBA_USER docker/prod.lock tmp/prod.lock

RUN micromamba \
  install --name base \
  --yes \
  -f tmp/prod.lock \
  && \
  micromamba clean --all --force-pkgs-dirs --yes

# clean up some stuff we dont't need for space
RUN find -name '*.a' -delete && \
  rm -rf /opt/conda/conda-meta && \
  rm -rf /opt/conda/include && \
  rm -rf /opt/conda/lib/libpython3*.so.1.0 && \
  find -name '__pycache__' -type d -exec rm -rf '{}' '+' && \
  rm -rf /opt/conda/lib/python3*/idlelib /opt/conda/lib/python3*/ensurepip \
    /opt/conda/lib/libasan.so.5.0.0 \
    /opt/conda/lib/libtsan.so.0.0.0 \
    /opt/conda/lib/liblsan.so.0.0.0 \
    /opt/conda/lib/libubsan.so.1.0.0 \
    /opt/conda/bin/x86_64-conda-linux-gnu-ld \
    /opt/conda/bin/sqlite3 \
    /opt/conda/bin/openssl \
    /opt/conda/share/terminfo && \
  find /opt/conda/lib/python3.10/site-packages/ -name 'tests' -type d -exec rm -rf '{}' '+' && \
  find /opt/conda/lib/python3.10/site-packages -name '*.pyx' -delete && \
  rm -rf /opt/conda/lib/python3.10/site-packages/uvloop/loop.c

ARG MAMBA_DOCKERFILE_ACTIVATE=1  # (otherwise python will not be found)

COPY --from=builder --chown=$MAMBA_USER:$MAMBA_USER /pkg/dist/ /pkg

RUN pip install /pkg/* --no-cache-dir

WORKDIR /data

ENTRYPOINT ["/usr/local/bin/_entrypoint.sh", "pycashier"]
