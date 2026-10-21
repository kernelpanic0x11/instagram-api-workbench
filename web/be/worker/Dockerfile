FROM node:22-bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends openjdk-17-jdk-headless procps curl ca-certificates && rm -rf /var/lib/apt/lists/*
RUN npm install --prefix /opt/rea rea-agents@6.7.0 --omit=dev --no-audit --no-fund
RUN mkdir -p /opt/jadx && curl -fsSL https://github.com/1013503897/jadx-headless-mcp/releases/download/v0.7.1/jadx-headless-mcp-0.7.1-all.jar -o /opt/jadx/engine.jar && echo '6e5eacf500b64292bfb73c49797c1958f6ee44646e43e868039ae7feb573ff75  /opt/jadx/engine.jar' | sha256sum -c -
ENV REA_JADX_MCP_JAR=/opt/jadx/engine.jar HOME=/tmp NODE_ENV=production
COPY entry.mjs /opt/worker/entry.mjs
COPY verify.mjs /opt/worker/verify.mjs
RUN mkdir -p /work && chown 10001:10001 /work
VOLUME ["/work", "/tmp"]
USER 10001:10001
WORKDIR /work
ENTRYPOINT ["node", "/opt/worker/entry.mjs"]
