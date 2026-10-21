# Reverse Engineer Anything — interactive prototype

Built from [arthelokyo/astrowind](https://github.com/arthelokyo/astrowind), MIT licensed. The analysis worker installs [REA](https://github.com/morluto/rea) from npm; upstream source archives are not bundled in this repository.

## Run

Use Node 22.22.3 or newer. Run `npm ci`, then `npm run dev -- --host 127.0.0.1`. Build with `npm run build`; validate with `npm run check`.

## Standalone review

After building, run `python3 scripts/export-standalone.py` from this directory to generate `../outputs/rea-prototype.html`. Generated review artifacts are not committed. Serve `dist/` over local HTTP for browser review. Static hosting serves the demo; the connected application needs the backend.

## Explore

- Start on Dashboard and open the Instagram example.
- Explore Overview, Evidence, and Files & links. Findings are illustrative fixtures.
- Review scope and complete demo checkout; each phase runs for 9–16 seconds.
- Pause/resume, simulate interruptions, retry at no charge, and simulate a refund.
- Create another investigation to exercise intake → local demo signup → free assessment.
- View saved projects, demo purchase history, theme settings, deletion and reset.
- Export a plain-text demo report. State survives reloads using localStorage.

## Connected application

The same build supports a connected application when served by `../be/server.mjs`. That server enables the live interface: Cognito sign-in, private persisted projects, real uploads, queued REA inspection, and Bedrock summaries. See [backend setup](../be/README.md) for configuration and verification status. AWS services and the analysis worker still require setup; the interface reports unavailable services explicitly.

## Static prototype boundaries

When served statically, there is no live REA analysis, Bedrock connection, server-side authentication, upload service, hosted job worker, or payment integration. The local demo profile is not an authenticated identity. Only file names and sizes are stored; file contents are never read. Reference URLs are stored as text and never fetched. Prices and timing are illustrative. The demo “background job” uses saved timestamps to advance when the page returns; it is not a persistent server process.

Production work requires isolated analysis workers, durable project/evidence storage and job orchestration, real identity and tenant isolation, upload/link validation, Bedrock orchestration, and idempotent payment/refund handling. REA provides MCP/CLI tools rather than this application layer. Progress should show activity and elapsed time; many REA operations have no known total. Recovery restores saved inputs and evidence rather than promising exact continuation of an interrupted native analysis.

AstroWind's typography, blue primary, Tailwind stylesheet, shared theme variables and shadcn-compatible tokens are retained. App-specific layout and interactions are in `src/assets/styles/workspace.css` and `src/scripts/workspace.ts`.
