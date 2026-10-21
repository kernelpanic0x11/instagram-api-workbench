import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, rm } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { generateKeyPair, SignJWT } from "jose";
import { createHash } from "node:crypto";
import { Store } from "../store.mjs";
import { loadConfig } from "../config.mjs";
import { CognitoAuth, verifyIdentity, digest, sessionFor } from "../auth.mjs";

const keys = await generateKeyPair("RS256");
const config = loadConfig({
  COGNITO_DOMAIN: "https://rea-test.auth.us-east-1.amazoncognito.com",
  COGNITO_CLIENT_ID: "test-client",
  COGNITO_USER_POOL_ID: "us-east-1_test",
  PUBLIC_ORIGIN: "http://127.0.0.1:8787",
});
const issuer = "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_test";
async function token(nonce, overrides = {}, signingKey = keys.privateKey) {
  return new SignJWT({
    sub: "subject-a",
    email: "alice@example.com",
    email_verified: true,
    name: "Alice",
    nonce,
    token_use: "id",
    ...overrides,
  })
    .setProtectedHeader({ alg: "RS256", kid: "test" })
    .setIssuer(issuer)
    .setAudience(config.clientId)
    .setIssuedAt()
    .setExpirationTime("10m")
    .sign(signingKey);
}

test("Cognito code flow binds state to its browser, checks PKCE, verifies identity, and rejects replay", async () => {
  const dir = await mkdtemp(path.join(os.tmpdir(), "rea-auth-"));
  const store = new Store(dir);
  try {
    let login;
    const auth = new CognitoAuth(config, {
      keys: keys.publicKey,
      fetcher: async (url, request) => {
        assert.equal(url.href, config.cognitoDomain + "/oauth2/token");
        assert.equal(request.body.get("grant_type"), "authorization_code");
        assert.equal(
          createHash("sha256")
            .update(request.body.get("code_verifier"))
            .digest("base64url"),
          new URL(login.url).searchParams.get("code_challenge"),
        );
        const saved = store.get("SELECT nonce FROM oauth_states LIMIT 1");
        // The one-time state is consumed before contacting the token endpoint.
        assert.equal(saved, undefined);
        return new Response(
          JSON.stringify({
            id_token: await token(nonce),
            access_token: "not-stored",
            refresh_token: "not-stored",
          }),
          { headers: { "Content-Type": "application/json" } },
        );
      },
    });
    login = auth.begin(store);
    const authorize = new URL(login.url);
    assert.equal(authorize.searchParams.get("code_challenge_method"), "S256");
    const nonce = authorize.searchParams.get("nonce");
    const callback = new URL(
      config.origin +
        "/auth/callback?code=one-time-code&state=" +
        authorize.searchParams.get("state"),
    );
    await assert.rejects(
      auth.callback(
        callback,
        { headers: { cookie: "rea_oauth=" + "x".repeat(43) } },
        store,
      ),
      /expired|already used/,
    );
    const result = await auth.callback(
      callback,
      { headers: { cookie: login.cookie.split(";")[0] } },
      store,
    );
    assert.equal(result.user.email, "alice@example.com");
    assert.ok(result.session.maxAge <= 600);
    assert.equal(store.all("SELECT * FROM oauth_states").length, 0);
    const session = sessionFor(
      { headers: { cookie: "rea_session=" + result.session.token } },
      store,
    );
    assert.equal(session.user_id, result.user.id);
    assert.notEqual(
      store.get("SELECT token FROM sessions").token,
      result.session.token,
    );
    assert.equal(
      JSON.stringify(store.all("SELECT * FROM sessions")).includes(
        "not-stored",
      ),
      false,
    );
    await assert.rejects(
      auth.callback(
        callback,
        { headers: { cookie: login.cookie.split(";")[0] } },
        store,
      ),
      /expired|already used/,
    );
    store.run(
      "DELETE FROM sessions WHERE token=?",
      digest(result.session.token),
    );
    assert.equal(
      sessionFor(
        { headers: { cookie: "rea_session=" + result.session.token } },
        store,
      ),
      null,
    );
  } finally {
    store.close();
    await rm(dir, { recursive: true, force: true });
  }
});

test("identity verification rejects forged signatures, wrong nonce, unverified email, and access tokens", async () => {
  const nonce = "expected-nonce";
  assert.equal(
    (await verifyIdentity(await token(nonce), config, nonce, keys.publicKey))
      .email,
    "alice@example.com",
  );
  await assert.rejects(
    verifyIdentity(await token("other"), config, nonce, keys.publicKey),
  );
  await assert.rejects(
    verifyIdentity(
      await token(nonce, { email_verified: false }),
      config,
      nonce,
      keys.publicKey,
    ),
  );
  await assert.rejects(
    verifyIdentity(
      await token(nonce, { token_use: "access" }),
      config,
      nonce,
      keys.publicKey,
    ),
  );
  const attacker = await generateKeyPair("RS256");
  await assert.rejects(
    verifyIdentity(
      await token(nonce, {}, attacker.privateKey),
      config,
      nonce,
      keys.publicKey,
    ),
  );
});

test("non-local HTTP deployment and non-Cognito identity endpoints fail closed", () => {
  assert.equal(
    loadConfig({
      COGNITO_DOMAIN: "https://auth.re.beehivewebstudio.com",
      COGNITO_CUSTOM_DOMAIN: "auth.re.beehivewebstudio.com",
    }).cognitoDomain,
    "https://auth.re.beehivewebstudio.com",
  );
  assert.throws(() => loadConfig({
    COGNITO_DOMAIN: "https://attacker.example.com",
    COGNITO_CUSTOM_DOMAIN: "auth.re.beehivewebstudio.com",
  }), /Cognito/);
  assert.throws(
    () => loadConfig({ PUBLIC_ORIGIN: "http://public.example.com" }),
    /HTTPS/,
  );
  assert.throws(
    () => loadConfig({ COGNITO_DOMAIN: "https://attacker.example.com" }),
    /Cognito/,
  );
});
