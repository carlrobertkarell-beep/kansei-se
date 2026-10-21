# Shoulder layer alignment review

All measurements use the original 1280 × 960 scan canvas. Clinical JPEGs and original finding SVGs remain byte-identical. Anatomy mode now uses the same original finding SVG in every bursa view.

| View | Action | Review |
| --- | --- | --- |
| Bursit, view 1 | Regenerated and globally registered | Fixed point (960,570) remains inside bursal fluid. Bone apex about (398,393) versus source (390,385); distal fluid tip about (1117,765) versus source (1117,767). Intermediate cortex and fluid interfaces retain about 15–30 px illustrative residual. Right outer scan margin is approximately 30 px narrower. Independent review accepted the tissue correspondence. |
| Bursit, view 2 | Regenerated and globally registered | Fixed point (610,415) remains inside fluid. Cortex peak about (696,523) versus source around (700,525); lower-left fluid tip around (252,765) versus source around (250,783). Most cortex/upper interfaces agree within about 5–20 px. |
| Supraspinatus | Regenerated and globally registered | Fixed defect points (689,502) and (745,463) remain within heterogeneous tendon defects. Original irregular-cortex point (953,488) is restored in anatomy mode, replacing the former relocated (978,517). Corresponding painted cortex is within about 15–20 px. Independent review accepted all three targets. |
| Subscapularis | Existing asset retained | Stump (265,435), residual-fiber region (770,620) and fluid (980,500) remain in the correct tissue. Fluid edge has about 10–15 px residual; focal cortex about 20 px. No material crossing requiring regeneration. |

The source contour guide is the existing clinician-derived `contours.20261016d.json`. Source guides and imagegen prompts are archived here. Each selected whole painting has exactly one recorded rectangular transform; no local warp or repeated texture atlas was used. The final published assets are opaque black-backed WebP images, with no acquisition header or guide lines.

`rebuild.py --qa-dir PATH` re-exports the selected archived WebP whole paintings using the recorded source bounds. It verifies the clinical-original hashes before rebuilding. The shared reader supplies the original/anatomy/findings controls and header clip.

To regenerate a guide PNG, render its source-guide SVG with Inkscape. The SVG links to the existing original JPEG through a repository-relative path. Original generated PNG filenames and hashes are retained in the manifest; duplicate raster copies are omitted.
