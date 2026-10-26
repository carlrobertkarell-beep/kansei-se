# Legacy URL and sitemap compatibility

The retired WordPress address
`/2024/03/01/att-lyfta-halsa-och-valbefinnande-i-stockholm-kraften-av-integrativa-program/`
now leads to `/rehabilitering/`. The current page covers individual programmes,
integrated treatment, progression and follow-up, making it a relevant replacement
for the old article's subject. This change does not recreate the original article.

GitHub Pages serves static files. The alias uses an immediate, zero-second HTML
meta refresh, a canonical URL and a visible fallback link, following the site's
existing legacy aliases. It is not an HTTP 301 response. Google documents instant
meta refresh as a permanent redirect when server-side redirects are unavailable:
https://developers.google.com/search/docs/crawling-indexing/301-redirects

The alias stays out of `sitemap.xml`. Unrelated missing URLs continue to return
the ordinary HTTP 404 page. The existing HTTP 301 from `https://kansei.se/` to
`https://www.kansei.se/` and the www canonical remain in place.

Four former WordPress sitemap addresses previously returned HTTP 404 after the
host redirect: `category-sitemap.xml`, `page-sitemap.xml`, `post-sitemap.xml` and
`post_tag-sitemap.xml`. They now serve XML sitemap indexes pointing only to the
current `https://www.kansei.se/sitemap.xml`. This preserves compatibility with old
submissions without duplicating URL lists or restoring obsolete WordPress URLs.
`robots.txt` continues to advertise only the current canonical sitemap.

The existing SEO check covers the article alias, target, exclusion from the
canonical sitemap, valid compatibility sitemap indexes and real 404 behaviour.
Its live mode also verifies the published alias and compatibility sitemap files.
