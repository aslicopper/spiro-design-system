# Spiro Figma Importer

A Figma plugin that imports the Spiro Design System (variables, text styles, effect styles, gradient paint styles, and components) into a Figma file. Safe to re-run — existing items are updated in place, deleted/renamed items are removed via the obsolete lists.

## Install (private)

1. Download `spiro-figma-importer.zip` from this folder (or the latest GitHub Release).
2. Unzip somewhere stable on your machine.
3. In Figma desktop: **Plugins → Development → Import plugin from manifest…** and select `manifest.json` from the unzipped folder.

For the design team to share the plugin without each member doing this manually, publish it as a private Organization plugin from the Figma UI once it's been imported by an admin.

## Run

Open the master Spiro Figma library file → Plugins → Development → Spiro Design System → click **Import to this file**.

Select which categories to import (Variables, Text, Effects, Gradients, Components) — usually keep all checked. The plugin reports created / updated / deleted counts when finished.

## Source

The plugin reads `tokens/figma-import.json`, which is the same source-of-truth file used by `@aslicopper/tokens` to generate CSS / Tailwind / W3C JSON. One edit, every consumer updates.
