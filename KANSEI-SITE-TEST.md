# Kansei site test 2026-09-15

This branch is an isolated Kansei website staging branch based on main commit `ade26e68d5f80679b06e09a5fb5d3c618ed775ed`.

Safety rules for this branch:
- Do not modify `/reda/`, `/reda2/`, Supabase migrations or Reda clinic/patient workspace code.
- Keep patient activation/login behavior exactly as inherited from `main`.
- Keep the public Reda destination `/reda-rehab/` inherited from `main` and marked as coming soon.
- Use the existing Reda brand assets from `/bilder/reda/`; the Kansei redesign may reference them but does not replace them.
- Do not merge test-only `noindex` or staging headers to production without an explicit production pass.

Scope of Kansei work:
- conversion-focused homepage and booking paths
- rich service pages while preserving existing SEO content
- contact flow: booking -> FAQ -> email/SMS; no private phone call CTA
- calmer page contents navigation
- shoulder and knee knowledge clusters
- optimized shared assets and lazy-loaded booking guide

Main remains untouched until explicit approval.
