# Embedded fonts, icons and installed artwork

The four original projects retain liixini's MIT license. The installed skwd-wall
SVG/logo is the unchanged project artwork from the pinned suite (source data and
MIT copyright notice accompany it). No personal wallpaper or external sample image
is part of these production packages. Deck templates are unchanged project files.
Lens model weights/ONNX Runtime are not bundled.

Wall embeds the suite's exact RobotoCondensed-Bold-{UI,SC,JP,AR,BN,HI}.ttf and
SymbolsNerdFont-Regular.ttf. No font bytes are changed by this legal repack.

* Roboto: Copyright 2011 The Roboto Project Authors, designer Christian Robertson,
  Google; https://github.com/googlefonts/roboto-3-classic, SIL OFL1.1.
* The upstream subset/merge script also draws from Noto Sans CJK (SC/JP), Noto
  Sans Arabic UI, Bengali UI, Devanagari UI and Noto Sans Symbols2. Credit Google,
  Adobe and the Noto Project contributors; https://github.com/notofonts/noto-cjk
  and https://github.com/notofonts/noto-fonts. Retain their OFL texts with the
  Roboto notice. The merged font's Roboto name table does not erase Noto rights.
  These were merged/subset upstream. The exact original Noto input-font build
  versions are not recorded by that script; no claim is made that this port
  regenerated those assets. Exact distributed font hashes remain pinned by the
  suite and source-delivery manifest. The public font-family licenses/attribution
  are retained separately. Derived primary names are Roboto Condensed, not a
  reserved Noto/Source/Pomicons/Font Awesome name.
* Symbols Nerd Font: copyright Ryan L McIntyre and contributing icon authors,
  Nerd Fonts3.4.0. The embedded file matches the official Git object exactly at
  fa7b859994228a9c8759f99c55a8d31ee92a1b5e. See nerd-font-match.json.
  Source: https://github.com/ryanoasis/nerd-fonts. No glyphs have been modified here.

Nerd icon attributions (upstream aggregation is not a blanket MIT relicense):

| Set | Author/project | Applicable notice |
|---|---|---|
| Codicons | Microsoft / vscode-codicons | CC BY4.0 |
| Devicons/Devicon | Theodore Vorillas and Devicon contributors | MIT |
| Font Awesome | Fonticons, Inc. | CC BY4.0 icons / OFL font terms retained |
| Font Awesome Extension | André Luiz Gava / contributors | MIT |
| Font Logos | Lukas-W / contributors | Unlicense (the audit's word “unlicensed” means this public-domain dedication, not missing permission) |
| Material Design Icons | Pictogrammers / Templarian and contributors | Apache2.0 |
| Seti/original | Jesse Weed, Ryan McIntyre and contributors | MIT |
| Octicons | GitHub / Primer contributors | MIT |
| Pomicons | Gabriele Lana | OFL1.1; primary font renamed by upstream |
| Powerline Extra | Ryan McIntyre / contributors | MIT |
| Powerline Symbols | Powerline contributors | Retained upstream free/MIT terms |
| IEC power symbols | Joe Loughry / Terence Eden / Unicode project contributors | MIT |
| Weather Icons | Lukas Bischoff, Erik Flowers and contributors | OFL1.1 font; README documentation CC BY3.0 |
| Extra glyphs | Hack / Source Foundry contributors | Original notices retained |

Complete upstream license, README attribution and audit files are retained in
assets/, including Supplemental notices for icon roots omitted by the release
archive. Their immutable source URLs/commits/hashes are in each source-delivery
manifest. Supplemental upstream references do not change the shipped glyph version.
CC BY requires credit, a license link/text and identification of modifications;
Nerd Fonts performed the aggregation/rescaling, and this port changes no glyphs.
The OFL font licenses continue to apply to fonts, independently of Skwd's MIT
code. No endorsement or trademark rights are claimed.

Weather Icons README documentation is unchanged and credited to Erik Flowers
and Lukas Bischoff; its CC BY3.0 license link is retained alongside the font OFL.
https://creativecommons.org/licenses/by/3.0/
