FROM node:22-bookworm-slim AS frontend
WORKDIR /app/fe
COPY fe/package*.json ./
RUN npm ci --no-audit --no-fund
COPY fe/ ./
RUN npm run build

FROM node:22-bookworm-slim
WORKDIR /app/be
COPY be/package*.json ./
RUN npm ci --omit=dev --no-audit --no-fund
COPY be/*.mjs ./
COPY --from=frontend /app/fe/dist /app/fe/dist
RUN mkdir /data && chown 10001:10001 /data
USER 10001:10001
ENV NODE_ENV=production HOST=0.0.0.0 DATA_DIR=/data FRONTEND_DIST=/app/fe/dist REA_EXECUTOR=fargate
EXPOSE 8787
CMD ["node", "--experimental-sqlite", "server.mjs"]
