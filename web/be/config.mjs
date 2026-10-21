import path from "node:path";

export function loadConfig(env = process.env) {
  if (
    env.NODE_ENV === "production" &&
    !env.PUBLIC_ORIGIN?.startsWith("https://")
  )
    throw new Error("Production requires an explicit HTTPS PUBLIC_ORIGIN.");
  const port = Number(env.PORT || 8787);
  const origin = env.PUBLIC_ORIGIN || `http://127.0.0.1:${port}`;
  const url = new URL(origin);
  if (url.origin !== origin || !["http:", "https:"].includes(url.protocol))
    throw new Error("PUBLIC_ORIGIN must be an origin without a path.");
  if (
    url.protocol !== "https:" &&
    !["127.0.0.1", "localhost", "[::1]"].includes(url.hostname)
  )
    throw new Error("Non-local deployments require HTTPS.");
  const region = env.AWS_REGION || "us-east-1";
  const cognitoDomain = env.COGNITO_DOMAIN || "";
  if (cognitoDomain) {
    const domain = new URL(cognitoDomain);
    if (
      domain.protocol !== "https:" ||
      domain.origin !== cognitoDomain ||
      (!domain.hostname.endsWith(`.auth.${region}.amazoncognito.com`) &&
        (!env.COGNITO_CUSTOM_DOMAIN || domain.hostname !== env.COGNITO_CUSTOM_DOMAIN))
    )
      throw new Error(
        "Use the HTTPS Cognito managed-login origin or the explicitly configured custom domain.",
      );
  }
  return {
    port,
    origin,
    secure: url.protocol === "https:",
    host: env.HOST || "127.0.0.1",
    dataDir: path.resolve(env.DATA_DIR || "./data"),
    staticDir: path.resolve(env.FRONTEND_DIST || "../fe/dist"),
    region,
    cognitoDomain,
    userPoolId: env.COGNITO_USER_POOL_ID || "",
    clientId: env.COGNITO_CLIENT_ID || "",
    modelId: env.BEDROCK_MODEL_ID || "",
    profile:
      env.AWS_PROFILE || (env.NODE_ENV === "production" ? undefined : "admin"),
    executor: env.REA_EXECUTOR || "docker",
    image: env.REA_WORKER_IMAGE || "rea-analysis:6.7.0",
    bucket: env.REA_WORKER_BUCKET || "",
    cluster: env.REA_ECS_CLUSTER || "",
    taskDefinition: env.REA_ECS_TASK_DEFINITION || "",
    subnets: (env.REA_ECS_SUBNETS || "").split(",").filter(Boolean),
    securityGroups: (env.REA_ECS_SECURITY_GROUPS || "")
      .split(",")
      .filter(Boolean),
    maxFileBytes: Number(env.MAX_FILE_BYTES || 268435456),
    maxProjectBytes: Number(env.MAX_PROJECT_BYTES || 1073741824),
    maxFiles: 16,
    jobTimeoutMs: 240000,
    modelTimeoutMs: 60000,
    maxModelTokens: 3000,
    maxEvidenceBytes: 524288,
    maxTextChars: 48000,
    sessionMs: 12 * 60 * 60 * 1000,
  };
}
