# Fieldnote upgrade report

Target repository: `https://github.com/hari-hashing/fieldnote`  
Target Pages URL: `https://hari-hashing.github.io/fieldnote/`

## Included

- Public discoverability: canonical URL, robots directives, Open Graph/Twitter metadata, CollectionPage JSON-LD, `robots.txt`, generated `sitemap.xml`, Atom `feed.xml`, and a crawlable static HTML landing page per indexed paper with ScholarlyArticle JSON-LD.
- Appearance: persistent System/Midnight/Light/Forest theme selection and six font presets (DM Sans, Inter, IBM Plex, Source Sans 3, Atkinson Hyperlegible, Space Grotesk).
- CI/CD: one workflow for PR validation, scheduled/manual research refresh, data commit, static build and GitHub Pages deployment. The older overlapping static/Jekyll deploy workflows are removed from the release bundle.
- Newsletter: Cloudflare Worker + D1 schema + Resend sender integration; explicit consent, double opt-in, editable IANA time zone, Wednesday 08:00–11:00 local-time delivery, one-per-local-week guard, idempotency keys and explicit confirmation/unsubscribe pages.
- Privacy page, deploy instructions, discovery guide and structural tests.

## Not activated by this bundle alone

- Changes are not yet pushed to GitHub. The GitHub connector currently returns HTTP 403 for repository Contents writes even though read access and repository admin metadata are visible.
- Google Search Console ownership verification and sitemap submission require the site owner's Search Console account.
- Newsletter sending requires the owner's Cloudflare account/D1 database, a Resend API key and a verified sender domain. The Worker URL and D1 ID remain placeholders. The public form stays inactive until the Worker is deployed and its URL is set in `assets/newsletter-config.js`.

## Validation performed

- Python compile checks: passed.
- JavaScript syntax checks (`app.js`, appearance preferences, newsletter client/config and Worker): passed.
- Static build: passed; 12 paper landing pages and 14 sitemap URLs generated from the bundled index.
- Data and build tests: passed (11 taxonomy bins, 12 indexed seed papers, 6 opportunity hypotheses).
- XML parsing: sitemap and Atom feed passed; Atom entry timestamps are RFC3339 UTC.
- Worker smoke tests: `/health` and disallowed-origin CORS rejection passed.
- Workflow YAML parsing: passed.

This is an upgrade overlay for the existing repository, not a replacement Git repository. See `APPLY-UPGRADE.md` before applying it.
