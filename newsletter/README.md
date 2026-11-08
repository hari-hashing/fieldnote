# Fieldnote newsletter service (Cloudflare Workers + D1 + Resend)

This is the actual email backend for the static site. It is separate from GitHub Pages because a static website cannot securely store email addresses or send email. It implements explicit consent, double opt-in, IANA time-zone validation, per-subscriber Wednesday scheduling, duplicate-send protection and unsubscribe links.

## Delivery behavior

- The browser auto-detects the visitor's IANA time zone (editable in the form).
- Subscribers choose Wednesday at 08:00, 09:00, 10:00 or 11:00 local time.
- A Cloudflare Cron Trigger runs every five minutes. Each run checks the local weekday/hour for every active subscriber, including DST-aware time-zone conversion.
- The D1 record stores the last sent local week to avoid duplicate weekly mail.
- Confirmation and digest emails are sent through Resend. Verification and unsubscribe links open explicit confirmation pages, so link-prefetching email scanners do not change subscriber state. Unsubscribed addresses remain suppressed.

## Deploy

1. From this folder, install Wrangler locally with `npm install --save-dev wrangler` (or use `npx wrangler`) and authenticate with `npx wrangler login`.
2. Create the database: `npx wrangler d1 create fieldnote-newsletter`; copy its `database_id` into `wrangler.toml`.
3. Apply schema: `npx wrangler d1 migrations apply fieldnote-newsletter --remote`.
4. Verify a sending domain in Resend, then update `FROM_EMAIL` in `wrangler.toml` to an address on that domain.
5. Store the provider key securely: `npx wrangler secret put RESEND_API_KEY`.
6. Deploy once: `npx wrangler deploy`. Copy the `workers.dev` URL printed by Wrangler and replace the `WORKER_URL` placeholder in `wrangler.toml`; deploy again with `npx wrangler deploy`. This URL is used by digest unsubscribe links.
7. Set `window.FIELDNOTE_NEWSLETTER_API` in the repository's `assets/newsletter-config.js` to the deployed Worker URL. Push the change to GitHub Pages.
8. Verify `/health`, complete a real double-opt-in sign-up and test a Wednesday subscriber before announcing availability.

Resend supports idempotency keys for email sends; the Worker uses stable per-confirmation and per-subscriber/week keys to reduce accidental duplicate sends. The D1 database ID, Cloudflare account and Resend API key are intentionally not included. Never commit subscriber data, `.dev.vars` or API keys.

## Security and operations

- CORS is restricted to `https://hari-hashing.github.io` by default.
- A honeypot field and a per-address rate limit reduce automated sign-up abuse.
- Verification tokens are stored as SHA-256 hashes; unsubscribe tokens are random and unguessable.
- The browser never receives subscriber records.
- Configure retention and deletion procedures for your applicable privacy obligations. A privacy notice is provided at `/privacy.html`.

## Time-zone precision

The five-minute cron checks subscriber-local time. Actual delivery can occur on the first cron execution during the selected hour, generally within five minutes after the hour begins. It is not a guarantee of second-level delivery.
