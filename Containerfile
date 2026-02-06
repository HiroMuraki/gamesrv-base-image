FROM debian:bookworm-slim AS builder
RUN apt update && apt install -y --no-install-recommends \
    tar \
    ca-certificates \
    wget &&\
    rm -rf /var/lib/apt/lists/*

WORKDIR /root/steamcmd
RUN wget https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz \
    && tar -xf steamcmd_linux.tar.gz

FROM debian:bookworm-slim

RUN apt update && apt install -y --no-install-recommends \
    lib32gcc-s1 \
    lib32stdc++6 \
    ca-certificates &&\
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /root/steamcmd /root/steamcmd
RUN /root/steamcmd/steamcmd.sh +quit
RUN mkdir -p /tmp/.steam/sdk32/ &&\
    ln -sf /root/steamcmd/linux32/steamclient.so /tmp/.steam/sdk32/steamclient.so

ADD ./gsrv.tar.gz /opt/gsrv

ENV JAVA_HOME=/opt/gsrv/runtime/java/25
ENV DOTNET_ROOT=/opt/gsrv/runtime/dotnet/10
ENV PATH="${DOTNET_ROOT}:${JAVA_HOME}/bin:/opt/gsrv:${PATH}"
