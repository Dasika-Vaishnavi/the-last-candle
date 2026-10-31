# PUBLISH THIS FOUR-STAGE GAME — READ FIRST

**This archive is the complete latest build:** Foyer, Library, Crypt, Kaashi finale; solo + multiplayer; the server-authoritative ghost/RPG systems and approved v2 visual style.

## Correct repository and folder

- Official repository: https://github.com/Dasika-Vaishnavi/the-last-candle
- Branch: **main**
- Your Render service is already configured to run the game from the **nested folder** `the-last-candle/`.
- Upload the *contents of this ZIP's `the-last-candle/` directory* into the repository's **existing** `the-last-candle/` directory.
- Do **not** make `the-last-candle/the-last-candle/`; Render would fail to find the server.
- Do **not** put the files only at repository root; the current Render build/start commands use `cd the-last-candle`.

## Easiest manual upload using GitHub web interface

1. Extract the archive to a folder on your computer.
2. Open https://github.com/Dasika-Vaishnavi/the-last-candle/tree/main/the-last-candle
3. Choose **Add file → Upload files** (or drag the updated project folder tree into the upload area).
4. Upload/replace `server.py`, `story_engine.py`, `crypt_engine.py`, `finale_engine.py`, `requirements.txt`, `render.yaml`, the complete `static/` folder, and the other included project files, all at the matching paths.
5. If GitHub's web upload refuses to overwrite existing files, use Git on your computer instead (commands below). A web upload *may* create duplicates or fail to replace files if you select the wrong folder.
6. Commit to `main`. Do not add secrets, `.env`, caches, or databases.

## Alternative: run the one-command publisher on your Mac

Download the `publish-current-stage4.sh` helper along with the ZIP and save both in `~/Downloads`. The script clones only the official repository, unpacks the exact ZIP into its existing nested folder, commits and pushes to `main` using your local GitHub authentication. It does not ask you to paste any passwords or tokens into this chat.

```bash
bash ~/Downloads/publish-current-stage4.sh
```

If you prefer the GitHub website instead, use the browser upload steps above. Either method updates the **same official GitHub repository**, never a different account.

## Verify the public build AFTER Render finishes auto-deploying

- Game: https://the-last-candle.onrender.com
- **Release check:** https://the-last-candle.onrender.com/health
- The health JSON MUST include `"release":"stage-4-complete"` and `"chapters":4`.
- If the release marker is absent, Render is still serving old code or the wrong GitHub folder was uploaded.
- Open a new private tab (or hard-refresh) to avoid an old cached frontend.
- Solo check: Enter Alone → Foyer → Library → Crypt → Kaashi finale; completing the Foyer should say **Continue into the darkness**, *not* "Stage 2 is coming soon."
- Multiplayer check: create room, join with second browser/device, verify synced timers and stage transitions.

## Sites frontend, if you publish it separately

`sites-frontend/` contains the HTML/CSS/JS for Sites. Do not deploy it as a Python backend.
The authoritative server remains on Render at `wss://the-last-candle.onrender.com/ws`.
Set `ALLOWED_WS_ORIGINS` to the exact published Sites origin in Render.
Do not assume there is a live ChatGPT Sites address unless you publish and verify one.

## Free-tier caveat

Render Free may sleep and resets in-memory rooms when it restarts or redeploys.
