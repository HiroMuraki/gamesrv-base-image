FROM moby/buildkit:latest

# 把证书复制到系统信任目录
# (注意：Alpine 系统是 /usr/local/share/ca-certificates，BuildKit 是 Alpine)
COPY .github/buildkit/server.crt /usr/local/share/ca-certificates/my-ca.crt

# 更新系统证书信任库
RUN update-ca-certificates