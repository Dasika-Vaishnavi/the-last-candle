# THE LAST CANDLE — ChatGPT Sites + Render Free deployment

**Current release:** Stage 4 complete: Foyer, Library, Crypt and Kaashi, solo + multiplayer, Ghost + RPG.

## Architecture

- **Sites:** `sites-frontend/index.html`, `sites-frontend/app.js`, `sites-frontend/styles.css`; visual rendering, sound and user input only.
- **Render Free:** `server.py` (`GET /health`, WebSocket `/ws`); room/seat identity, roles, clues, randomized puzzles, timer, wrong-answer penalties, hints, solo Lens, cooperative levers and rhythm.
- The Sites website connects to **`wss://the-last-candle.onrender.com/ws`**.
- The full server remains running on Render. ChatGPT Sites cannot execute the existing persistent Python server itself.

## Step 1 — Publish backend source to the OFFICIAL GitHub repository

The official repository is **https://github.com/Dasika-Vaishnavi/the-last-candle**.

The full source is under an existing GitHub directory `the-last-candle/`. Upload/replace the contents of the bundled `the-last-candle/` directory at that same path. **Do not add another nesting level.** This must include `server.py`, `crypt_engine.py`, `story_engine.py`, `static/`, `sites-frontend/`, `tests/`, `requirements.txt`, `render.yaml`, and `SITES_DEPLOY.md`. Do not upload `game.sqlite3`, `.env`, `__pycache__`, or `.pytest_cache`.

The existing Render web service (`the-last-candle`, **plan: free**, auto-deploy `main`) currently runs:

- **Build:** `cd the-last-candle && pip install -r requirements.txt`
- **Start:** `cd the-last-candle && python server.py`
- **URL:** https://the-last-candle.onrender.com

Commit the upload to `main` and inspect Render's new auto-deploy until status is `live`. Confirm `https://the-last-candle.onrender.com/health` returns `{"status":"ok", ...}`. No persistent disk is required or provisioned. Room state is in memory and is lost after restart.

## Step 2 — Create and publish the ChatGPT Site

Open ChatGPT **Work / Sites** on web or desktop. Start a Site based on the `sites-frontend/` folder from this release (or import the `the-last-candle-sites-frontend.zip` package). Preserve all supplied HTML/CSS/JS and do not generate a new backend. Request a **public** website. Review its preview, publish, and copy its actual HTTPS URL. Sites publishing capability is not exposed in every chat environment; its URL is only known after a successful Sites deployment.

The frontend uses the current Site's `location.origin` to generate invite links like:

`https://<actual-sites-host>/?room=ABCD`

The private solo reconnect URL uses `?solo=<private-room-id>`, with the seat secret held in that device's session storage. The room code/private room ID is not a substitute for a secret seat token.

## Step 3 — Allow the exact Sites origin in Render

Get the published Sites URL and extract its origin: scheme + domain, **no path**. In the existing Render `the-last-candle` web service, set:

`ALLOWED_WS_ORIGINS=https://<actual-sites-domain>`

If there are multiple approved Sites origins, separate with commas. Do **not** use `*` or assume a domain before publication. The backend rejects browser WebSocket upgrades from unapproved origins with HTTP 403. `GET /health` returns `Access-Control-Allow-Origin` only for approved origins. WebSocket authentication still requires the server-issued seat token to rejoin.

**Optional only after Sites multiplayer tests pass:** Set `SERVE_FRONTEND=0` in Render to serve backend-only `/health` and `/ws`; the default is `1` so the existing Render frontend URL remains a usable fallback until Sites works.

If the published Site blocks outbound WebSockets via Content Security Policy, update its `connect-src` policy to allow `wss://the-last-candle.onrender.com`, if available, then retest. No amount of backend CORS configuration can override a browser CSP restriction.

## Step 4 — Public acceptance tests

**Two-device multiplayer:**

1. On phone A, visit the **actual Sites URL**, create a 2-player circle and copy its invitation.
2. On laptop B or another phone, open the invitation. Verify it points to **Sites**, not Render.
3. Enter a second name. Confirm both devices show both players with live presence dots.
4. Choose two complementary roles, ready up, start. Confirm candle and stage stay synced, hints and wrong-answer penalties apply once on both devices.
5. Solve the Foyer, continue to the Library, decode the cipher and hold both levers together 3 seconds. Confirm both clients advance simultaneously. Continue into the Crypt, have Wren follow the guide through the seeded maze, check shared trap penalties and Sure Step, then reach the sealed exit.
6. Refresh a device and confirm the same seat is restored. Leave and resume to verify host migration if needed.

**Solo:** Visit the Sites URL, choose Enter Alone, equip two powers, start the 25-minute timer, switch between five Lenses, solve the Foyer, Library, and Crypt, and refresh mid-switch to verify recovery. In the Crypt, Ember sees left traps, Vesper right traps, and only Wren can move.

**Cold start:** Close active tabs and allow Render to idle, then open the Sites URL. The themed **Waking the spirits…** screen must remain until the socket is ready; the WebSocket retries automatically. The 25-second client heartbeat works while an active browser connection is open, but cannot prevent all free-tier restarts.

## Local test suite

From the root of the game directory with Python and Node installed:

```bash
python -m pip install -r requirements.txt
PORT=8765 python server.py &  # needed for the existing network acceptance tests
python -m pytest -q tests
node tests/test_ui_render.cjs
node tests/test_sites_client.cjs
node tests/test_story_ui.cjs
node tests/test_crypt_ui.cjs
```

The Python tests include allowed/denied WebSocket Origin, two shared room clients, and solo rejoining through a Sites-origin connection. They test the bridge locally, not the unpublished ChatGPT Sites URL.

## Release guardrails

1. Run all tests and fix failures.
2. Commit to `Dasika-Vaishnavi/the-last-candle` on `main`.
3. Verify Render Free auto-deployed and `/health` responds.
4. Deploy the matching `sites-frontend/` to the **same ChatGPT Site**.
5. Test real devices and share the verified Sites URL.

The two deployments are not atomic; keep the previously working site/release active until both sides pass. Render Free may sleep/restart, so strict continuous availability requires a more durable hosting plan.

## Stage 4 Sites frontend

The Stage 4 frontend is included under `sites-frontend/` with the exact same `app.js` and `styles.css` as the integrated Render frontend. Its `index.html` sets `TLC_SITES_FRONTEND=true` and points WebSockets at `wss://the-last-candle.onrender.com/ws`. It cannot run independently of a **matching Stage 4 backend**.

Publish the entire Sites frontend to the already-selected ChatGPT Sites project, then add the *actual* Sites origin to Render's `ALLOWED_WS_ORIGINS` (comma-separated exact `https://` origin). Do not guess the Sites domain. Test two browser devices joining one circle and completing at least the Three Streams / secret offering before sharing the Sites link. Keep the previous published version live until both new deployments pass validation. On Render Free, restarts clear all in-memory rooms regardless of host frontend.
