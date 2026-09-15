# Coherent clinic preview, not a production migration

Builds a static, isolated preview from the original rich clinic content. The previous deployment mixed new homepage/contact pages with legacy clinic/blog/service templates; passing source CI did not catch that user-visible mismatch.

The builder installs the same static header/footer and accessible animated menu on content-bearing Swedish clinic pages, turns /kunskapsbank/ into a real searchable hub, and renders existing /blogg/ article URLs in the new template. /om-oss/ stays the canonical clinic destination, linked directly from both desktop and mobile navigation. Original titles, canonicals and H1 are asserted unchanged, except for the formerly redirected knowledge hub. Full service/article bodies are retained instead of replaced with summaries.

Run:

```
python .github/kansei-preview/build.py . /tmp/kansei-preview/public
python .github/kansei-preview/browser_check.py /tmp/kansei-preview/public /tmp/kansei-preview/results
```

Dependencies in the preview workflow are pinned. Browser checks must run against generated output over HTTP, not the untouched source templates. Failure blocks deployment.

All output is noindex and protected by the existing Netlify access policy. No production mode is provided. Reda applications, patient workspaces, Supabase and activation are excluded. Reda product pages and English landing are intentionally not redesigned here. Existing patient portal redirects to the official production origin; no duplicate connected app is deployed.

This is a corrected review candidate, not a claim that the complete site is final, SEO ranking improved, or physical Safari/iPhone/performance testing finished. Production needs its own reviewed build/indexing/redirect pass and explicit owner approval. Do not merge staging noindex settings to main.
