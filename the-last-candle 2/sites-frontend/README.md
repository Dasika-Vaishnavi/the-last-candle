# THE LAST CANDLE — ChatGPT Sites frontend

Use this directory as the website source in ChatGPT Sites. It is a static
HTML/CSS/JavaScript frontend; **do not migrate the Python game state here**.

## Integration

- Backend (existing Render Free service): `https://the-last-candle.onrender.com`.
- WebSocket: `wss://the-last-candle.onrender.com/ws`.
- Set the Render environment variable `ALLOWED_WS_ORIGINS` to the **exact** public
  origin of your ChatGPT Site (for example, `https://<actual-site>.chatgpt.site`).
  Do **not** guess the origin or enable `*`.
- This frontend uses `/?room=ABCD` invites to avoid depending on static hosting
  path rewrites. Solo refresh links use `/?solo=<private-room-id>`.
- Publish the Site with public/anyone-with-link access when intended.
- A Site host may apply an outbound Content Security Policy; allow `connect-src`
  to `wss://the-last-candle.onrender.com` if Sites exposes that configuration.
- Keep `/health` and 25-second WebSocket heartbeat on Render. The waking screen
  automatically retries cold start connections.
- Browser console must show no CSP or mixed-content blocking errors.

## Scope and caveats

- Original multiplayer/gameplay UI stays unchanged in the combined Render app.
- This frontend renders projections from the authoritative backend, never answers.
- Render Free may idle/restart and lose in-memory rooms.
- Actual ChatGPT Sites URL must be obtained from a successful Sites publish.
- After publishing, verify two real devices can create/join and stay synced.
