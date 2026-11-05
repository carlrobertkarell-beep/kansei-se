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

The current 79.166667-second November 5 web edition
`sinovial-sinogel-pris-bokning.20261105.mp4` preserves the approved film-7
cut, product inserts and original recorded voice. Its price card shows
Sinovial HL 64: SEK 2,490 for one joint / SEK 4,980 for two joints;
Sinogel: SEK 2,990 for one joint / SEK 5,980 for two joints, at the same visit.
The price scene at approximately 39.5–52.3 seconds replaces the old dated
card, including its short transition frames, without changing the running time.
The delivery copy uses H.264 (CRF 23) with the original audio copied unchanged.
Swedish speech captions and chapter timings remain in the October 20 VTT
files because the spoken script and timing are unchanged. The original
October 20 MP4 is retained but no longer referenced by public HTML or sitemaps.
Update the price card and matching page metadata together when prices change.
