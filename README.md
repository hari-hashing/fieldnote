# Fieldnote — Embodied AI Research Atlas

A GitHub Pages research portal for Vision-Language Models (VLMs), Vision-Language-Action Models (VLAs), world models, World-Action Models (WAMs), and adjacent embodied robotics research.

## What is included

- **11-bin taxonomy:** multimodal perception; spatial grounding; embodied reasoning; VLA architectures; world models; WAMs; data/pretraining; policy learning/RL; modalities and embodiments; systems/deployment; evaluation/safety.
- **Paper library:** search, filter, primary-bin classification, secondary tags, source and status labels, direct paper/code links, metadata export.
- **Research opportunities:** practical, falsifiable hypotheses at underrepresented bin intersections, with a problem statement, hypothesis, minimum experiment, resources, risks and novelty caveat.
- **Idea deep-dive lab:** turns an opportunity into a model-ready research brief prompt covering the literature audit, novelty, theory, architecture, code, experiments, compute, risk and deliverables.
- **Persistent archive:** dated snapshots in `data/archives/YYYY-MM-DD.json`, a cumulative `data/papers.json`, and an archive manifest.
- **Automation:** GitHub Actions ingests recent papers daily, updates the JSON index and archive, rebuilds the static site and deploys it to GitHub Pages.

The site is static HTML/CSS/JavaScript. No application server, database, framework build or paid hosting is required.

## Deploy on your GitHub account

1. Create a new repository, for example `embodied-ai-atlas` (public repositories are the simplest GitHub Free Pages option).
2. To create a new repository and push from a machine with Git and GitHub CLI installed, run `gh auth login`, then from this project directory run `./scripts/publish.sh YOUR_GITHUB_USERNAME/embodied-ai-atlas public`. The helper refuses to run if this folder already has a Git repository or remote, so it will not silently overwrite an existing project. Alternatively, create an empty repository on GitHub and push the project contents to its default branch manually. Keep the `.github/workflows/` directory.
3. In the repository, open **Settings → Pages → Build and deployment → Source**, and select **GitHub Actions**.
4. Open **Actions** and enable workflows if GitHub asks. Run **Update and deploy research atlas** once using **Run workflow**.
5. After the workflow succeeds, the environment/deployment summary shows the published Pages URL. It normally has the form `https://<owner>.github.io/<repository>/`.

The included workflow listens to pushes to `main`, manual runs, and a daily schedule. If your default branch is not named `main`, update the branch under `on.push.branches` in `.github/workflows/research-atlas.yml` before pushing.

The scheduled run is daily at 02:17 UTC (07:47 India Standard Time). GitHub Actions scheduled events can be delayed during high load; manual dispatch is available as a fallback.

## Data sources and verification policy

| Source | How it is used | Evidence status |
|---|---|---|
| arXiv Atom API | Recent submissions from `cs.RO`, `cs.CV`, `cs.AI`, `cs.LG`, plus targeted all-category searches | Primary preprint metadata |
| OpenReview API 2 | Recent public notes/submission records; current API sample is filtered locally | Primary platform record; decision/venue status must be checked |
| OpenAlex Works API | Broad discovery for records that may be missed by category searches | Discovery only; stays `needs_verification` until its publisher/preprint source is checked |

The ingestion pipeline uses a seven-day publication/submission window by default. It deduplicates by arXiv identifier, DOI or normalized title. The full local index accumulates over time; daily archives preserve a seven-day rolling snapshot and source counts for that run. Re-running the workflow on the same UTC date refreshes that day’s snapshot; prior dates remain stored. If a source is unavailable or rate-limited, the workflow records a warning and continues where possible. The archive does not claim exhaustive internet coverage.

**Important limitations:**
- The arXiv index is based on the configured categories and search expressions, and the OpenReview fetch samples recent public records. Neither can guarantee every relevant item on every platform is found.
- OpenAlex is an aggregator, not a primary source. Those results are visibly flagged for verification.
- Automatic binning is a keyword-based first pass. It is useful for navigation, not a substitute for human classification. Existing curated primary bins are preserved.
- Peer review, real-robot evaluation, benchmark details, code availability and author claims must be confirmed from the actual paper. Missing information is labelled as unverified rather than guessed.
- Research-opportunity scores are based on the coverage of intersections in this repository's current corpus and a manually assigned feasibility prior. They are **not** novelty scores and cannot prove that no one has worked on an idea.

## Optional model-assisted research ideas

The site works without an LLM key. The default opportunity engine refreshes coverage counts and gap heuristics from the paper index.

To also generate new candidate ideas from the latest indexed corpus, configure these GitHub repository settings:

- **Settings → Secrets and variables → Actions → Secrets:** `OPENAI_API_KEY`
- **Settings → Secrets and variables → Actions → Variables:** `OPENAI_MODEL` (a model identifier available to your API account)
- Optional variable: `OPENAI_BASE_URL` (defaults to `https://api.openai.com/v1`; may be set to another OpenAI-compatible endpoint)

The optional `scripts/enrich_opportunities.py` job sends paper titles, abstracts, taxonomy labels and existing opportunity cards to the configured endpoint. It validates returned evidence IDs against the local index and retains a novelty caveat. Never commit API keys to this repository. Review model-generated ideas manually; generation is not a verified novelty search.

## Run locally

Requires Python 3.10+ for the update scripts. The updater uses only the Python standard library.

```bash
# From the repository root
python scripts/update_research.py --days 7
python scripts/build_site.py
python -m http.server 8000
```

Open `http://localhost:8000`. For a site build preview independent of the repo root, serve `_site` after running `build_site.py`.

Useful manual options:

```bash
python scripts/update_research.py --days 14
python scripts/update_research.py --days 7 --skip-openalex
python scripts/update_research.py --days 7 --skip-openreview
```

## Repository map

```text
.
├── index.html
├── assets/                    # Static UI
├── data/
│   ├── taxonomy.json
│   ├── papers.json            # Cumulative index
│   ├── opportunities.json    # Research leads and coverage scores
│   ├── manifest.json         # Archive index
│   └── archives/YYYY-MM-DD.json
├── scripts/
│   ├── publish.sh          # Optional safe first-publish helper (requires GitHub CLI)
│   ├── update_research.py    # arXiv + OpenReview + OpenAlex ingestion
│   ├── enrich_opportunities.py # Optional model-assisted ideation
│   └── build_site.py
└── .github/workflows/
    └── research-atlas.yml    # Daily update + GitHub Pages deployment
```

## Suggested contribution workflow

1. Check the primary paper and code before editing metadata.
2. Keep one primary bin, add multiple secondary bins, and explain the primary scientific contribution.
3. Record first submission date separately from latest revision date or conference acceptance.
4. Mark `real_robot` as `Not established` unless the paper explicitly demonstrates physical-hardware experiments.
5. Add any manually curated record to `data/papers.json`; run the build and inspect filters, links and mobile layout.
6. Treat proposed research directions as hypotheses. Add closest related work and a falsification experiment before presenting a novelty claim.

## License and attribution

The frontend and ingestion scripts in this repository are provided under the MIT License. Paper titles, abstracts, bibliographic metadata and author-provided material remain the property of their respective authors/publishers and are linked to their original sources. Do not mirror paper PDFs unless their licenses permit it.


## Public discovery, themes and newsletter

The project is a public GitHub repository. The build creates a crawlable HTML landing page for each indexed paper, canonical metadata, ScholarlyArticle structured data, `robots.txt`, `sitemap.xml` and an Atom feed. These help search-engine discovery but do not guarantee indexing. See `docs/DISCOVERABILITY_AND_RELEASE.md` and submit the sitemap through Google Search Console after deployment.

Visitors can choose System, Midnight, Light or Forest themes and DM Sans, Inter, IBM Plex, Source Sans 3, Atkinson Hyperlegible or Space Grotesk fonts. Preferences are stored locally in the browser.

The weekly newsletter uses the separate Cloudflare Worker/D1 + Resend service in `newsletter/`. It supports double opt-in, an editable IANA time zone, Wednesday delivery between 08:00 and 11:00 local time, weekly duplicate protection and unsubscribe links. Follow `newsletter/README.md`. Set both `WORKER_URL` in `newsletter/wrangler.toml` and `window.FIELDNOTE_NEWSLETTER_API` in `assets/newsletter-config.js` after the first Worker deploy. The signup form stays inactive until the Worker URL and sender setup are configured.

The single CI/CD workflow validates pull requests, refreshes research on scheduled/manual runs, builds crawlable paper pages and deploys to GitHub Pages. The older overlapping `static.yml` and Jekyll workflows have been removed to prevent competing deployments.
