# Third-party notices

The root MIT license covers original project code. It does not relicense third-party software, application binaries, or extracted evidence.

See [Instagram third-party notices](apps/instagram/THIRD_PARTY_NOTICES.md) for the existing workbench's dependencies and analyzed application. Future apps should keep their own notices beside their implementation.

The original Instagram reverse-engineering work used [REA (Reverse Engineer Anything)](https://github.com/morluto/rea) by [morluto and contributors](https://github.com/morluto/rea/graphs/contributors), alongside JADX and custom DEX analysis scripts. Credit to the REA project for the analysis tooling that supported this research. REA is used as an external tool; its implementation and downloaded analysis engines are not bundled in this repository.

The selected Discord bytecode analysis uses separately downloaded [P1sec/hermes-dec](https://github.com/P1sec/hermes-dec) (AGPL-3.0-or-later). Its implementation is not bundled. Native instruction excerpts were produced with [LLVM](https://llvm.org/). See [deep-analysis notes](docs/DEEP_ANALYSIS.md) for exact tool versions and scope. Extracted app identifiers and instruction excerpts retain their respective owners’ rights.
