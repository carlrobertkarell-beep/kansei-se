# Ultrasound anatomy-layer audit — 21 October 2026

Scope: coordinate registration, tissue-region continuity, finding overlays and reader presentation. No new clinical diagnoses were inferred. The clinical ultrasound images remain the reference.

The actual reader HTML contains **12 case pages, 38 static-view occurrences and 35 unique image pairs**. The three runner views appear on both the knee and runner pages. The inventory therefore counts them once. Videos are outside the static-image count.

**22 new versioned assets** comprise 21 rebuilt continuous paintings and one cleaned existing painting registered to its clinical source. **13 paintings were retained.** Every unique clinical original matches the recorded git baseline byte for byte. [inventory.json](inventory.json) records all 35 original hashes, anatomy hashes, dimensions, decisions and reader occurrences.

| Case reader | Static views in this reader | Result |
|---|---|---|
| Biceps | Transverse; longitudinal (2) | Both rebuilt and globally registered. Small tendon/fascial regions retained. |
| Pectoralis | Longitudinal; transverse (2) | Both rebuilt and registered to original capture geometry. |
| Carpal tunnel | Medianus (1) | Existing tissue painting retained, embedded labels cleaned, then globally registered. |
| AC joint | Injured comparison; opposite comparison; AC joint; soft-tissue plane (4) | Four continuous paintings rebuilt and globally registered; source-coordinate labels and consistent finding overlays. |
| Calcific shoulder | Examined side; reference side (2) | Both rebuilt and registered. Three detail windows use the original crop rectangles in both modes. The same corrected asset is reused by the three overview/demo pages. |
| Shoulder bursa | Bursa 1; bursa 2; supraspinatus; subscapularis (4) | First three rebuilt/registered; subscapularis retained. |
| Knee | Effusion; Baker; meniscus; cartilage comparison; osteophytes; cartilage detail; lateral fluid; ITB bursa; posterior meniscus (9) | Five native knee views rebuilt/registered; native meniscus retained. Last three reuse the runner paintings below. |
| Runner knee | ITB bursa; lateral fluid; posterior meniscus (3) | Three mesh/collage assets replaced by continuous paintings, globally registered. |
| Hip joint | Capsule; femoral head; side comparison (3) | Accepted `20261021c` paintings retained from the preceding correction. Source integrity and shared full-frame presentation checked. |
| Gluteal tendons | Gmed; Gmin; paralabral (3) | All retained following source/painting/finding review. |
| Achilles | Longitudinal; reference side; transverse (3) | All paintings retained. One malformed transverse SVG boundary corrected. Doppler remains a separate video. |
| Elbow | Examined side; reference side (2) | Both paintings retained after native-frame/crop checks. Reference side explicitly has no pathology markers. |

## Source-coordinate corrections

- **Achilles transverse:** two lower-edge y values had been inserted into the upper boundary. `L502 180 L514 437 L526 433 L538 166` became `L502 180 L514 175 L526 171 L538 166`. This removes an artificial deep spike. The clinical image and painting are unchanged. Source: [gluteal-achilles/review.json](gluteal-achilles/review.json).
- **AC joint pointers:** shadow, coloured pointer and target dot now end together. The AC target is `(735,250)`; the soft-tissue target is `(660,116)` following the visible upper separation. Native comparison calipers and their published distances were preserved. Both image modes use the same finding geometry. Source: [ac/registration.json](ac/registration.json).
- **Knee:** mode-specific displaced finding groups were removed; the original coordinate layer is shared by ultrasound and anatomy. Anatomy was registered to those coordinates.
- **Knee labels/materials:** five rebuilt native views have source-coordinate anatomy labels without obsolete leader arrows. The cartilage-detail central tendon material was corrected to ivory while the upper-left muscle remained red; its 17 reviewed lower-contour anchors are within 13.9 pixels of the source guide. Source: `knee/labels.20261021f.json` and `knee/cartilage-detail/registration.json`.
- **Reader frame:** full-stage paintings no longer inherit the former subrectangle placements on the upper-limb pages. Runner and elbow original/anatomy transforms remain identical through their cropped viewport and enlarged view. Anatomy labels yield to findings and return when findings are off.

## Evidence and limits

Visual review used untouched originals, paintings, and source-coordinate outlines/pointer targets. The new exports use one global rectangular placement per whole painting, with a scan clip; no triangular texture meshes or local tissue warps. Relevant prompts, source guides, material references, registration bounds and hashes are recorded in `upper-limb/`, `ac/`, `shoulder/`, `knee/`, and the sibling `../runner/` archive.

Registration is approximate. Reviewed local contour differences are generally about 5–30 source pixels; some retained gluteal boundaries and the bursa-1 intermediate cortex are at the upper end. A common whole-image shift would worsen other matched boundaries. Reviewers found no main finding-target swap between tissue regions; this is not a claim of pixel-perfect correspondence or clinical validation. Tissue colour, fascia and internal bone material remain illustrative.

The reproducible static check is:

```sh
python .github/kansei/ultrasound_layer_check.py --base 44a309fa45471b9120b830c6c7fed7a015f3fe0d --output /tmp/ultrasound-layers.json
```

It verifies immutable clinical bytes against the selected git revision, decodes all anatomy assets, checks their native dimensions against HTML, and compares actual geometry/ancestor transforms for paired clinical finding layers. It also rejects stale mode-specific knee groups. Result at this snapshot: 35 originals unchanged; 35 anatomy assets valid; 15 paired-identical finding layers, 22 shared layers, and one explicitly unmarked healthy elbow view. These layer counts include the three repeated runner occurrences.

Final static integration checks passed after preview-build cleanup: six guard tests; SEO/internal-target/JSON-LD checks (202 HTML files, 269 JSON-LD blocks, 133 sitemap URLs); visibility checks; nine reader script syntax checks; Python compilation; whitespace checks. The parent task also reported successful enlarged knee osteophyte/cartilage interaction checks and 390-pixel knee, AC and biceps focus screenshots with no horizontal overflow and correct label focus. This is scoped interaction/layout evidence, not exhaustive browser coverage of every view.
