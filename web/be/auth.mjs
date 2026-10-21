import {
  randomBytes,
  createHash,
  timingSafeEqual,
  randomUUID,
} from "node:crypto";
import { createRemoteJWKSet, jwtVerify } from "jose";
export const digest = (value) =>
  createHash("sha256").update(value).digest("hex");
export const secret = () => randomBytes(32).toString("base64url");
export const readCookie = (req, name) =>
  (req.headers.cookie || "")
    .split(";")
    .map((s) => s.trim())
    .find((s) => s.startsWith(`${name}=`))
    ?.slice(name.length + 1) || "";

export function sessionFor(req, store) {
  const token = readCookie(req, "rea_session");
  if (!/^[a-zA-Z0-9_-]{43}$/.test(token)) return null;
  return (
    store.get(
      "SELECT sessions.*,users.email,users.name FROM sessions JOIN users ON users.id=sessions.user_id WHERE token=? AND expires>?",
      digest(token),
      Date.now(),
    ) || null
  );
}
export function newSession(
  user,
  store,
  config,
  expires = Date.now() + config.sessionMs,
) {
  const token = secret(),
    csrf = secret();
  const until = Math.min(Date.now() + config.sessionMs, expires);
  store.run(
    "INSERT INTO sessions(token,user_id,csrf,expires) VALUES(?,?,?,?)",
    digest(token),
    user.id,
    csrf,
    until,
  );
  return {
    token,
    csrf,
    maxAge: Math.max(0, Math.floor((until - Date.now()) / 1000)),
  };
}
export function sessionCookie(token, config, clear = false, maxAge = 3600) {
  return `rea_session=${clear ? "" : token}; Path=/; HttpOnly; SameSite=Lax; Max-Age=${clear ? 0 : maxAge}${config.secure ? "; Secure" : ""}`;
}
export function requireMutation(req, session, config) {
  if (req.headers.origin !== config.origin)
    throw Object.assign(new Error("Request origin is not allowed."), {
      status: 403,
    });
  if (session) {
    const supplied = Buffer.from(String(req.headers["x-csrf-token"] || ""));
    const actual = Buffer.from(session.csrf);
    if (supplied.length !== actual.length || !timingSafeEqual(supplied, actual))
      throw Object.assign(
        new Error("Your session has changed. Reload and try again."),
        { status: 403 },
      );
  }
}
export async function verifyIdentity(token, config, nonce, keys) {
  const issuer = `https://cognito-idp.${config.region}.amazonaws.com/${config.userPoolId}`;
  const { payload } = await jwtVerify(token, keys, {
    issuer,
    audience: config.clientId,
    algorithms: ["RS256"],
    requiredClaims: [
      "exp",
      "iat",
      "sub",
      "nonce",
      "token_use",
      "email",
      "email_verified",
    ],
    maxTokenAge: "1h",
  });
  if (
    payload.token_use !== "id" ||
    payload.nonce !== nonce ||
    payload.email_verified !== true ||
    typeof payload.email !== "string" ||
    typeof payload.sub !== "string"
  )
    throw new Error("Identity claims did not match the sign-in request.");
  return {
    subject: `${issuer}|${payload.sub}`,
    email: payload.email.toLowerCase(),
    name:
      typeof payload.name === "string"
        ? payload.name.slice(0, 80)
        : payload.email.split("@")[0],
    expires: Number(payload.exp) * 1000,
  };
}
export class CognitoAuth {
  constructor(config, { fetcher = fetch, keys } = {}) {
    this.config = config;
    this.fetcher = fetcher;
    this.configured = Boolean(
      config.cognitoDomain && config.clientId && config.userPoolId,
    );
    if (this.configured)
      this.keys =
        keys ||
        createRemoteJWKSet(
          new URL(
            `https://cognito-idp.${config.region}.amazonaws.com/${config.userPoolId}/.well-known/jwks.json`,
          ),
          { timeoutDuration: 10000 },
        );
  }
  begin(store) {
    if (!this.configured)
      throw Object.assign(
        new Error(
          "Cognito sign-in is not configured yet. Your draft remains in this browser.",
        ),
        { status: 503 },
      );
    const state = secret(),
      verifier = secret(),
      nonce = secret(),
      binding = secret();
    store.run("DELETE FROM oauth_states WHERE expires<?", Date.now());
    store.run(
      "INSERT INTO oauth_states(state,binding,verifier,nonce,expires) VALUES(?,?,?,?,?)",
      digest(state),
      digest(binding),
      verifier,
      nonce,
      Date.now() + 600000,
    );
    const url = new URL("/oauth2/authorize", this.config.cognitoDomain);
    url.search = new URLSearchParams({
      response_type: "code",
      client_id: this.config.clientId,
      redirect_uri: `${this.config.origin}/auth/callback`,
      scope: "openid email profile",
      state,
      nonce,
      code_challenge: createHash("sha256").update(verifier).digest("base64url"),
      code_challenge_method: "S256",
    }).toString();
    return {
      url: url.href,
      cookie: `rea_oauth=${binding}; Path=/auth; HttpOnly; SameSite=Lax; Max-Age=600${this.config.secure ? "; Secure" : ""}`,
    };
  }
  async callback(url, req, store) {
    if (!this.configured)
      throw Object.assign(new Error("Cognito sign-in is not configured."), {
        status: 503,
      });
    const state = url.searchParams.get("state") || "",
      binding = readCookie(req, "rea_oauth");
    if (
      !/^[a-zA-Z0-9_-]{43}$/.test(state) ||
      !/^[a-zA-Z0-9_-]{43}$/.test(binding)
    )
      throw Object.assign(
        new Error(
          "The sign-in request is missing or expired. Start sign-in again.",
        ),
        { status: 400 },
      );
    const pending = store.transaction(() => {
      const saved = store.get(
        "SELECT * FROM oauth_states WHERE state=? AND binding=? AND expires>?",
        digest(state),
        digest(binding),
        Date.now(),
      );
      if (!saved)
        throw Object.assign(
          new Error(
            "The sign-in request is missing, expired, or already used.",
          ),
          { status: 400 },
        );
      store.run("DELETE FROM oauth_states WHERE state=?", digest(state));
      return saved;
    });
    const code = url.searchParams.get("code");
    if (!code || code.length > 4096 || url.searchParams.has("error"))
      throw Object.assign(
        new Error("Sign-in was not completed. Please try again."),
        { status: 400 },
      );
    const response = await this.fetcher(
      new URL("/oauth2/token", this.config.cognitoDomain),
      {
        method: "POST",
        redirect: "error",
        signal: AbortSignal.timeout(10000),
        headers: { "content-type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({
          grant_type: "authorization_code",
          client_id: this.config.clientId,
          code,
          redirect_uri: `${this.config.origin}/auth/callback`,
          code_verifier: pending.verifier,
        }),
      },
    );
    if (!response.ok)
      throw Object.assign(
        new Error(
          "Cognito did not complete the sign-in exchange. Start sign-in again.",
        ),
        { status: 401 },
      );
    const tokens = await response.json();
    const identity = await verifyIdentity(
      tokens.id_token,
      this.config,
      pending.nonce,
      this.keys,
    );
    // Tokens stay in request memory. No access, ID, or refresh token is stored in the browser or database.
    let user = store.get(
      "SELECT * FROM users WHERE subject=?",
      identity.subject,
    );
    if (!user) {
      user = { id: randomUUID(), email: identity.email, name: identity.name };
      store.run(
        "INSERT INTO users(id,email,name,subject,created) VALUES(?,?,?,?,?)",
        user.id,
        user.email,
        user.name,
        identity.subject,
        Date.now(),
      );
    } else {
      store.run(
        "UPDATE users SET email=?,name=? WHERE id=?",
        identity.email,
        identity.name,
        user.id,
      );
      user = { ...user, email: identity.email, name: identity.name };
    }
    const prior = sessionFor(req, store);
    if (prior) store.run("DELETE FROM sessions WHERE token=?", prior.token);
    const session = newSession(user, store, this.config, identity.expires);
    return { session, user };
  }
  logoutUrl() {
    if (!this.configured) return this.config.origin;
    const url = new URL("/logout", this.config.cognitoDomain);
    url.search = new URLSearchParams({
      client_id: this.config.clientId,
      logout_uri: this.config.origin + "/",
    }).toString();
    return url.href;
  }
}
