FROM eclipse-temurin:25-jre AS jre-25
FROM eclipse-temurin:21-jre AS jre-21
FROM eclipse-temurin:17-jre AS jre-17
FROM eclipse-temurin:8-jre AS jre-8

FROM debian:bookworm-slim

ARG DEFAULT_PUID=1000
ARG DEFAULT_PGID=1000

ENV TZ=Asia/Shanghai
ENV JAVA_VERSION=25

RUN apt update && apt install -y \
    gosu \
    ca-certificates

COPY --from=jre-8 /opt/java/openjdk /opt/runtime/jre-8
COPY --from=jre-17 /opt/java/openjdk /opt/runtime/jre-17
COPY --from=jre-21 /opt/java/openjdk /opt/runtime/jre-21
COPY --from=jre-25 /opt/java/openjdk /opt/runtime/jre-25

RUN groupadd -g ${DEFAULT_PGID} gsrv
RUN useradd -u ${DEFAULT_PUID} -g ${DEFAULT_PGID} \
    -d /opt/gsrv \
    -m \
    -s /bin/bash \
    gsrv

RUN mkdir -p /app && chown gsrv:gsrv /app

WORKDIR /app

COPY ./entrypoint /bin/entrypoint
RUN chmod +x /bin/entrypoint

ENTRYPOINT ["entrypoint"]
