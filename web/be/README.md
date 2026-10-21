# REA phase-zero service

This service connects the approved AstroWind interface to Cognito sign-in, durable owner-scoped projects, streamed source uploads, a persistent job queue, isolated REA inspection, and Bedrock evidence summaries. It does not enable paid phases or free-form chat.

## Local setup

Use Node 22 LTS, version 22.22.3 or newer. The local development machine currently has Node 22.22.0 and an additional Node 26 installation; use the LTS runtime for this service. A direct run under the system Node 26.7.0 crashed inside Node's native async runtime during testing; the documented `npm test` path passes.

1. Run `npm ci` in this directory and `npm ci` in `../fe`.
2. Build the interface with `npm run build` in `../fe`.
3. Refresh the selected AWS profile: `aws login --profile admin`.
4. Deploy Cognito and populate non-secret IDs with `python3 ../scripts/configure-aws.py --profile admin --region us-east-1 --origin http://127.0.0.1:8787`.
5. Copy any remaining settings from `env.example` into `.env`, preserving the generated Cognito IDs. Set `BEDROCK_MODEL_ID` to a tool-capable model or inference profile accessible to this account. No model is silently selected.
6. Start Docker and run `npm run worker:build`. The worker installs `rea-agents@6.7.0`, JDK 17, and the SHA-256-verified JADX engine pinned by REA.
7. Run `npm start`, then open `http://127.0.0.1:8787`.

The account/goal flow is intake → Cognito managed sign-in/signup → saved project → source material → explicit start → real activity/evidence → report and unpriced next scope. Cognito owns verification, recovery, and passwords. AWS access, ID, and refresh tokens stay in callback memory; they are not persisted or placed in browser storage. The app sets an opaque HttpOnly session cookie with SameSite=Lax, expiring no later than the Cognito ID token. Production requires HTTPS and Secure cookies. Sign-out revokes the app session and redirects through Cognito logout.

## Custom sign-in domain

The approved login domain is `auth.re.beehivewebstudio.com`. From `web/`, run `python3 scripts/configure-auth-domain.py` with the refreshed local `admin` profile. It provisions the separate `rea-auth-domain` CloudFormation stack in `us-east-1`: a DNS-validated ACM certificate, Cognito custom domain, and Route 53 alias. It preserves the existing user pool, app client, and callback configuration. The setup only switches `be/.env` after HTTPS discovery is available; then restart this service.

Cognito requires a resolvable parent domain. If `re.beehivewebstudio.com` has no A or CNAME record, the script creates the AWS-documented `198.51.100.1` placeholder with a 60-second TTL. Replace that record when hosting the application; it does not currently serve the app. Existing parent records are preserved. The backend accepts a custom login origin only when it matches the explicit `COGNITO_CUSTOM_DOMAIN` setting. JWT validation continues to use Cognito's regional issuer and JWKS.

## Isolation and evidence

Local analysis runs as UID 10001 in a read-only Docker container with no network, no capabilities, no-new-privileges, bounded CPU/memory/PIDs/output/time, ephemeral writable directories, and no host mounts or AWS credentials. Only two commands are allowlisted: `inspect-artifact` and `inspect-android-package`. User files are data, never executable applications. APK selection is based on the uploaded name and still requires the analyzer to validate its contents. Unknown target formats fail explicitly.

The worker persists each successful REA output, source SHA-256, source ID, and job ID before the model call. Bedrock receives bounded evidence context and a strict assessment schema. Every finding must cite an existing evidence ID. Reports distinguish observations from inferences, include unknowns, expose omitted inputs, and leave pricing unquoted. Up to three files are inspected per free assessment, with a four-minute overall deadline, one model call, a 60-second model timeout and a 3,000-token output cap. Each account may queue ten free jobs per day and one active job at a time. These are resource limits, not a guarantee of complete analysis.

## Persistence and ownership

SQLite, source files, sessions, and OAuth state live under `DATA_DIR` (default `./data`). The directory is private; database/source files use owner-only permissions. Use encrypted persistent storage and backups for hosting. The service supports one active worker per database and is intended for a single application instance; it is not a horizontally scaled SaaS deployment.

Every project, source, evidence, report, mutation, and export checks the signed-in owner's ID server-side. Mutations require the exact configured Origin and a session-bound CSRF token. Links are stored but never fetched, avoiding a URL-fetch/SSRF surface. HTML renders escaped user/model/tool text. OAuth uses PKCE, random one-use state bound to a separate browser cookie, nonce, trusted JWKS, issuer/audience/signature/expiry/token-use/email-verification checks, and session rotation.

Deleting a source removes its bytes but preserves reports and evidence. Deleting a project cancels its job and removes its local source bytes, evidence, report, and job history. In-flight workspace cleanup is asynchronous; Fargate staging objects are explicitly deleted after work and have a one-day recovery lifecycle for interrupted cleanup. This first version does not implement account deletion or operational backup erasure.

Jobs survive browser closure. On service restart, an expired job lease can restore inputs and rerun the bounded step; this is not exact continuation of an in-flight decompilation. Goal changes cancel active work, increment revision, preserve earlier reports, and prevent stale results from being published to the new scope.

## AWS-hosted workers

`REA_EXECUTOR=fargate` uses the infrastructure in `../infra/analysis-stack.json`. Build/push the worker image to an ECR repository named `rea-analysis` first. The stack accepts that pinned image URI, an existing VPC/subnet, and the regional S3 managed prefix list. It creates a private encrypted transient bucket, ECS cluster/task, execution role, restricted security groups and private ECR/CloudWatch endpoints. Endpoint resources have ongoing charges; the template is prepared but has not been deployed or cost-validated.

The Fargate task has no task IAM role. It receives only short-lived, object-specific S3 URLs. The web service's AWS runtime identity needs Bedrock invocation, access to its transient bucket, ECS RunTask/DescribeTasks/StopTask on the configured cluster/task definition, and iam:PassRole restricted to the generated execution role and ECS service. Production should use a scoped runtime role; `admin` is the user-selected local setup profile. The task's egress is limited to S3 and private image/logging endpoints. Real ECR pull, writable-volume permissions, REA/JADX, Fargate cancellation/cleanup, and Bedrock inference still need provider verification before public rollout.

The application image is defined in `../infra/Dockerfile` and expects a durable `/data` volume, an HTTPS reverse proxy, and its public origin/Cognito/worker environment settings. It does not mount a Docker socket. Use the Fargate executor in that image. Frontend/API/auth callback must share one origin; the static Sites prototype alone cannot host this Node/SQLite service.

## Verification

Run `npm run worker:build` then `npm run worker:verify` to check the actual pinned REA provider under the application's Docker isolation settings. The check statically inspects the base image's `/usr/bin/true` ELF file, verifies its SHA-256 and evidence envelope, and requires explicit limitations. It never executes that target. This check passed locally on October 20, 2026. Android/JADX, Bedrock, and the complete signed-in assessment flow still need live verification. Launch the backend from your own terminal if the agent sandbox prevents its child processes from accessing Docker.

Run `npm test`. Tests exercise the real HTTP server and database, signed Cognito-like JWT validation, PKCE/state/nonce/replay checks, session revocation, two-user isolation, CSRF, real streamed file hashing and limits, evidence retention/deletion, citation validation, and cancellation of stale work. Analyzer and token-exchange fixtures are explicitly injected in tests only; they do not establish live AWS or REA behavior. No environment switch enables fake authentication or demo findings in the live service.

Run `npm run check` and `npm run build` in `../fe`. The original interactive prototype is retained when served statically; this backend injects live mode into the same built interface. The live mode does not silently fall back to demo data if the API fails.
