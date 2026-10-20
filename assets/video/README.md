# Shared standard for spoken clinic films

Use a clean video without baked speech captions on the website. Keep the approved
audio, clinical illustrations and scene labels. Supply the approved Swedish speech
as a synchronized WebVTT file, with a default `track` of kind `captions` and the
label `Svenska` inside `video.film-player`.

Include `/assets/film.20261019c.css` and the deferred
`/assets/film-captions.20261019.js` on every page embedding these films, including
overview pages. The shared player displays 17–19 px captions below the picture on
screens up to 640 px wide. Larger players, fullscreen and picture-in-picture use
the native caption track. The player's CC setting controls both presentations;
native captions also remain available without JavaScript.

Keep the visible transcript, VideoObject, share metadata, poster, chapter links
and media sitemap in sync with the published video. Use new asset filenames after
changing video, captions or poster. Separate downloadable/social masters can keep
baked captions when they need to work outside the website player.

Add each new film page to `FILM_PATHS` in
`.github/kansei/film_caption_check.py` and its expected duration. Browser checks
cover playback, synchronized captions, CC off/on, small-screen layout and
fullscreen at 320, 390 and 1440 px widths.

## Light and colour

The October 20 web editions use a gentle lift in shadows and midtones, with black
and white anchored. Match each insert to the talking sections rather than giving
every camera source the same exposure change. Keep natural skin, white surfaces
and navy clothing; avoid a yellow skin cast or a washed-out picture. Ultrasound
detail and the approved anatomy artwork keep their existing contrast.

`.github/scripts/grade-hyaluron-films.py` records the exact scene-specific curves
for films 1 and 3. It starts from the clean October 19 web editions and copies
the audio without re-encoding. New films should be matched to this visual tone
before captions and export.

## Film 7: Sinovial and Sinogel

The 79.166667-second October 20 web edition uses the approved film-7 cut,
product inserts, price graphic and original recorded voice. Its delivery copy
is encoded as H.264 with the audio copied unchanged. Swedish speech captions
and chapter timings are separate VTT files; the standalone review copy has
burned captions. The price graphic is dated October 20, 2026. Update that
graphic and the matching caption/page metadata together when prices change.
