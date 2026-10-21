# Mobile App API Workbench

A workspace for reverse-engineered mobile app research, evidence, and local API tooling. The repository retains its existing `instagram-api-workbench` GitHub URL.

The original Instagram reverse-engineering work used [REA (Reverse Engineer Anything)](https://github.com/morluto/rea) by [morluto and contributors](https://github.com/morluto/rea/graphs/contributors), alongside JADX and custom DEX analysis scripts. Credit to the REA project for the analysis tooling that supported this research.

| App | Directory | Status |
| --- | --- | --- |
| Instagram | [apps/instagram/](apps/instagram/) | Existing workbench, analysis scripts, and evidence |
| Snapchat | [apps/snapchat/](apps/snapchat/) | Reserved; no implementation |
| Discord | [apps/discord/](apps/discord/) | Reserved; no implementation |
| TikTok | [apps/tiktok/](apps/tiktok/) | Reserved; no implementation |
| Roblox | [apps/roblox/](apps/roblox/) | Reserved; no implementation |

Each app owns its tooling, dependencies, documentation, evidence, and local analysis inputs. Instagram-specific code remains in its app directory; no shared runtime is introduced yet.

Run the existing Instagram workbench from the repository root:

```sh
cd apps/instagram/api
node server.mjs
```

Open http://127.0.0.1:8766/. See the [Instagram guide](apps/instagram/README.md) for setup, validation, reproduction, and research limitations. Previously root-relative Instagram commands now run from `apps/instagram/`.

The [REA web application](web/README.md) lives in `web/`: an AstroWind interface, Cognito-backed service, isolated analysis worker, and AWS templates. Its setup and verification status are documented separately from the app-specific research workbenches.

Repository-wide public artifact check:

```sh
python3 scripts/check-public.py
```

Original code is MIT licensed; app evidence and bundled dependencies retain their own rights. See [LICENSE](LICENSE) and each app's notices.
