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
