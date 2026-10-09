# Review — mvanhorn/last30days-skill @ a3b73fc5f3fb3a464d6dfb7660eec7ef1dc6d366 (v3.27.1)

authority=false · read-only review · nothing installed or executed · 2026-10-09
Method: shallow fetch of the pinned commit into a scratch folder; read SKILL.md, references/setup-wizard.md,
references/runtime.md and grepped scripts/ (580 files) for installs, credential access, update checks and endpoints.
Not a full audit: the engine (scripts/lib, ~100 modules) was searched, not read line by line.

## What runs, and when
| Behaviour | Where | Default |
|---|---|---|
| First-run setup wizard | SKILL.md "FIRST_RUN_DETECTED … read the setup-wizard immediately" | **automatic** on first invocation |
| `brew install yt-dlp` | scripts/lib/setup_wizard.py `run_auto_setup` | runs during **Auto setup** if Homebrew exists |
| `npx -y @mvanhorn/printing-press-library@0.1.16 install digg / arxiv / techmeme --cli-only` | setup_wizard.py `_install_digg_cli`, `install_default_pp_sources` | runs during **Auto setup** (`-y` = no npm prompt); package version pinned |
| Browser cookie extraction (x.com auth_token/ct0) from Chrome/Brave/Edge/Vivaldi/Opera/Arc | setup_wizard.py, cookie_extract | **only with explicit consent** (`allow_browser_cookies`, `FROM_BROWSER`); "a skip or no answer is never consent" |
| `agentcookie` sidecar reads X cookies "automatically" if that CLI is installed | setup-wizard.md l.202 | off unless installed; `AGENTCOOKIE=off` disables |
| ScrapeCreators signup via GitHub device flow; key persisted to `~/.config/last30days/.env` | setup-wizard.md Step 4 | offered, opt-in; 10,000 free calls then pay-as-you-go |
| Update | Claude Code marketplace install: plugin cache auto-refreshes on new releases; SKILL.md hops to a newer cached copy | **auto-update if installed from the marketplace**; none for a manual clone or uploaded .skill |
| Writes | `~/Documents/Last30Days/` briefs, `~/.config/last30days/.env` (mode 0600), SQLite (watchlist only), temp plan files | always (briefs, config) |
| Publishing | `ht-ml.app` hosted library, public by default | only on explicit request |

## Sources without any credential ("Skip for now" path)
Reddit (with comments), Hacker News, Polymarket, GitHub, web search (host). `Skip for now` writes
`SETUP_COMPLETE=true` and `BROWSER_CONSENT=false` and runs **no setup command** (no brew, no npx).
YouTube needs yt-dlp (local); X, TikTok, Instagram, Bluesky, Perplexity need credentials or cookies.

## Network endpoints seen in scripts/lib (sample)
reddit.com, arctic-shift.photon-reddit.com, hn.algolia.com, gamma-api.polymarket.com, api.github.com, x.com, api.x.ai,
api.scrapecreators.com, youtube.com, di.gg, techmeme.com, bsky.social, api.perplexity.ai, openrouter.ai, api.openai.com,
r.jina.ai, trustpilot.com, threads.net, plus local host.docker.internal (Xiaohongshu).

## Conditions for a manual trial (proposed)
1. Install by **manual clone pinned to a3b73fc** + symlink, not via the marketplace (no auto-refresh).
2. At the wizard, choose **Skip for now**: no installs, no cookies, no keys. Optionally run `--preflight` first.
3. Run once, by hand, on "agentic AI / agentic operating systems"; the brief must state which platforms were actually covered
   (expected: Reddit, HN, Polymarket, GitHub, web; not X, TikTok, YouTube transcripts).
4. Read the brief before any scheduling decision. A 30-day version check, if wanted, is a **notification for review**
   (compare the pinned SHA with the repo HEAD), never an install.
