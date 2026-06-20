# Changelog

All notable changes to the MSP Pure Water report generator.

## [1.4.0] — Hardness audit, sales-focused reports & honest grading
### Changed
- **Audited and corrected hardness for 30 metro cities** against DROP, dakotawater, premier &
  Bethel data — notably **Maple Grove 7 → 25 gpg** (it does not soften), plus Plymouth, Chaska,
  Minnetonka, Edina, Victoria, Wayzata, Lakeville, Rosemount, Farmington, Bloomington and more.
  Eden Prairie verified at ~6 gpg (it runs a softening plant).
- **Reports now show only contaminants MSP systems remove** — reassuring "Normal" rows are
  dropped; the table lists just the treatable problems (hardness always shown).
- **Recalibrated grading** so municipal water never reads A/B+ (effective ceiling ~C+); hardness
  dominates the score. Verdicts are problem-focused; the "good news" section pivots to the sale.
### Tests
- 38 cases (added Maple-Grove-is-hard, no-inflated-grades-anywhere, problems-only-table).

## [1.3.0] — Search, history, tests & docs
### Added
- **Search by address, city, or ZIP** with city autocomplete, common aliases
  (`St Paul`, `mpls`), in-address city detection, and fuzzy "did you mean?" suggestions.
- **Searchable Recent Reports** panel — filter past reports by city/ZIP/address and re-download.
- **System photos** — upload a photo per system (or drop `assets/systems/<key>.png`); it appears
  on the recommended-system page when that system is recommended.
- **Test suite** — 36 `unittest` cases covering parsing, resolution, ratings, recommendations,
  data integrity, and PDF generation.
- Comprehensive `README.md` and this changelog.
- CLI now accepts city/address queries and `--list-cities`.

## [1.2.0] — Real units, safe levels & correct products
### Changed
- Contaminant table is now **Contaminant · Your Est. Level · Normal/Safe Level · Rating** with
  real units (gpg/ppm/ppb/pCi/L/ppt); dropped the "Treated By" and "EPA Standard" columns.
- Ratings (Normal/Elevated/High/Concerning) are now **consistent with the safe level shown**.
- Product catalog rebuilt to the real lineup: Standard Softener + Carbon, Dual-Tank City,
  Dual-Tank Well, Hydrogen Peroxide, Salt-Free + Carbon, with 7-Stage (AlkaPro) / Tankless RO.
- **Recommendation rule fixed**: city water → Standard; Dual-Tank City is a large-home upsell
  only (6+ residents & 4+ baths); dual-tank/peroxide are for wells; softened cities → Salt-Free.
- Real phone (952-952-6206) and trust badges (Made in USA, Lifetime Warranty, NSF, BBB).

## [1.1.0] — Full metro data & accuracy
### Fixed
- **ZIP-based city resolution** — postal-city names no longer mislabel suburbs
  (e.g. Brooklyn Park ZIPs reported as "Minneapolis"). Added core-ZIP guards.
### Added
- ~95 Twin Cities metro cities with researched finished hardness and source type.
- Result-page table contained in a responsive scroll wrapper.

## [1.0.0] — Initial release
- Branded multi-page PDF report from a ZIP, with a Flask website and CLI.
- Vector MSP shield logo (auto-replaced by an uploaded `logo.png`).
- Curated Twin Cities water knowledge base, East Metro PFAS detection, hardness & TDS,
  contaminant assessment, and whole-home + RO solution positioning.
