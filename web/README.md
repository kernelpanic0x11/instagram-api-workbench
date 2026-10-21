# Reverse Engineer Anything web application

REA turns an application and a goal into a saved investigation with source material, evidence, phased findings, and a proposed next scope. The interface is built from [AstroWind](https://github.com/arthelokyo/astrowind); the isolated worker installs [rea-agents](https://github.com/morluto/rea) from npm at version 6.7.0. App-specific research remains in the repository's `apps/` directory.

## Layout

- `fe/`: Astro/TypeScript interface, including the interactive static demo and connected workspace.
- `be/`: Cognito sign-in, owner-scoped SQLite storage, uploads, job queue, Bedrock orchestration, worker, and tests.
- `infra/`: Cognito and Fargate CloudFormation templates and the application Dockerfile.
- `scripts/`: AWS setup helpers. They resolve paths relative to this directory.

## Run

Use Node 22 LTS, version 22.22.3 or newer. From this directory:

```sh
npm ci --prefix fe
npm ci --prefix be
npm run build --prefix fe
cd be
cp env.example .env
npm start
```

Open http://127.0.0.1:8787. Configure Cognito, Bedrock, and the analysis executor using the [backend guide](be/README.md). Those services are not enabled by copying the sample configuration. The custom-domain helper currently contains the project owner's deployment domain and hosted-zone ID; adapt it before using another AWS account.

For the static interactive demo, run `npm run dev --prefix fe` from this directory and open the displayed address. Demo sign-in, findings, checkout, and timing are illustrative. The connected backend does not fall back to demo data.

## Validation and status

```sh
npm test --prefix be
npm run check --prefix fe
npm run build --prefix fe
```

The backend suite contains 11 tests. A real isolated REA ELF inspection has passed; Android/JADX, Bedrock inference, and the complete Cognito signup-to-assessment flow still need live verification. Paid phases and free-form AI chat are not connected. AWS worker hosting has not been deployed or verified. See the backend guide for resource limits and data handling.

Run `python3 scripts/check-public.py` from the repository root before publishing. Credentials, environment files, SQLite databases, uploads, downloaded engines, generated outputs, and browser state are excluded. Keep the AstroWind license in `fe/LICENSE.md`.
