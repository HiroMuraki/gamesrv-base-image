FROM python:3.14-slim AS builder

ENV PYTHONUNBUFFERED=1

COPY ./deploy_jres.py /data/deploy_jres.py
COPY ./jre-pkgs.toml /data/jre-pkgs.toml

WORKDIR /data

RUN --mount=type=cache,target=/tmp/jre-pkg \
    python ./deploy_jres.py

FROM debian:bookworm-slim

ENV TZ=Asia/Shanghai
ENV JAVA_VERSION=25

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update &&\
    apt-get install -y tzdata

COPY --from=builder /data/runtime /opt/runtime

COPY ./entrypoint /bin/entrypoint
RUN chmod +x /bin/entrypoint

VOLUME ["/app"]

ENTRYPOINT ["entrypoint"]
