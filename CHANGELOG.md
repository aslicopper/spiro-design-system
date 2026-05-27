# Changelog

All notable changes are documented here. The format is based on [Keep a Changelog](https://keepachangelog.com/) and the project follows [SemVer](https://semver.org/).

## 0.16.0 — 2026-04-25

Initial public bundle. Everything below was promoted from the in-house preview build.

### Added
- `@aslicopper/tokens` package with CSS variables, ESM/CJS constants, W3C tokens.json, and a Tailwind preset.
- `@aslicopper/react` package with the `Button` component.
- `@aslicopper/figma-plugin` distribution (.zip).
- 353 colour variables across Light / Dark modes; spacing / radius / stroke / opacity number scales; 9 elevation shadows; 28 text styles; 45 gradient paint styles; 14 components.
- Build script `packages/tokens/scripts/build.cjs` that regenerates every dist artifact from `packages/tokens/src/tokens-studio.json` (the Tokens Studio for Figma source of truth).

### Fixed
- Light-theme shadow CSS variables now declared inside `:root` (previously sat inside the dark block, leaving light mode with no shadows).
