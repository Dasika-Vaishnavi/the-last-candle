# THE LAST CANDLE — Stage 4 Finale (Foyer · Library · Crypt · Kaashi)

A playable, server-authoritative four-stage Victorian horror escape-room game for **2–5 players together or one player alone**. **No accounts. No install for players. Original CSS/SVG art.**

## Included

### Solo — Enter Alone

- Landing offers **Gather a Circle** for the unchanged multiplayer flow, **Enter Alone** for a private single-seat chamber, and a smaller link to join an existing circle.
- Solo is created immediately with no lobby invite code or share action. An anonymous secret in the tab's `sessionStorage` restores the same solo seat on refresh (`/solo/<private-id>`). Other browsers cannot join a solo room.
- Solo prep shows Vesper, Quill, Ember, Crowe and Wren's original Gothic portraits. **Choose exactly two once-per-round abilities**; every character's information remains available through their Lens regardless of which abilities were equipped. Wren's ability is for Stage 3 and cannot be used during the Foyer.
- **25-minute solo candle**, validated by the same server timer and penalties as the 20-minute multiplayer candle.
- A five-portrait **Lens switcher** stays at the bottom of solo gameplay. The client sees only the active character's clues. Switching Lens takes **two real seconds** and triggers an original smoke wipe; the server gates clue disclosure and action permissions until the switch finishes. The candle keeps burning during the switch unless an equipped Ember power is actively freezing time.
- Use **Quill** for diary hours, **Ember** for symbol order, and **Crowe** to submit the clock code. Hints and incorrect-code penalties work the same as the team mode.
- Solving each room advances through the Library, Crypt, and Kaashi finale. Completing all four awards a **separate solo full-game rank** and an ending at Hollow Manor at dawn.
- `TRY_AGAIN` returns to solo ability selection with a new seeded puzzle. Nothing in this mode changes multiplayer role locks or gameplay.

### Multiplayer — Gather a Circle (unchanged)

- Mobile-first hand-drawn Gothic landing screen (approved Patrick Hand and Nunito fonts, flat-color SVG style)
- Four-letter lobby codes, capacity 2–5, role selection, ready states, live presence, invite links and host migration
- Anonymous seat recovery across refreshes and temporary disconnections using a per-tab `sessionStorage` credential
- Assigned/mixed role reveal cards, with private role-specific Foyer clues and clear "What you can see / What you must do" instructions
- Server-authoritative 20-minute never-pausing candle, versioned synchronized state, clock dials, server-checked code, and atomic −30-second wrong-answer penalties
- Three escalating, public 60-second hints (requested by any player; no voting)
- Foyer completion with synchronized chime and door; playable Library cipher/levers, Crypt maze and Kaashi finale with shared full-game ending
- Built-in spirit-board text chat; opt-in, generated wind/heartbeat/chime/ghost audio (sound off by default)
- Seed-randomized diary death hours and new solution each round; same-group replay
- In-memory room state (resets on Render free-tier restart); HTTP `/health` health check and `/ws` readiness probe
- Rate-limited room admission, authoritative role permissions, unique action IDs, cooldown against answer spam

## Run locally

Requires Python 3.10+.

```bash
cd the-last-candle
python -m pip install -r requirements.txt
python server.py
```

Open **http://localhost:8080**. If port 8080 is already in use, start with `PORT=8765 python server.py` and use http://localhost:8765 instead.

For other phones on the **same Wi-Fi**, run the server bound to your LAN address (the default listens on all network interfaces) and open `http://YOUR-COMPUTER-LAN-IP:8080` on each device. Modern browsers may restrict clipboard and other permissions without HTTPS. For remote players across networks, deploy to HTTPS hosting as below.

## Test SOLO with one tab

1. Open `http://localhost:8080` and click **Enter Alone**. A private solo preparation room appears automatically, with no four-letter code shown.
2. Choose **exactly two abilities** (for example Vesper and Crowe); **Begin Alone** becomes enabled. The character information from the other three remains available in-game regardless of ability selection.
3. Press **Begin Alone**, read the role reveal, and click **Open Your Eyes**. The candle starts at 25:00.
4. The bottom **Lens** bar has five portraits. You begin as Vesper. Choose Quill, wait through the 2-second smoke transition, and note the four diary hours. Switch to Ember, wait two seconds, and note the scratch-symbol order. Switch to Crowe and enter the hours in that order.
5. Try a wrong combination to check the −30-second penalty; reveal a hint to check −60 seconds. Solve the puzzle, wait for the door to open, click **Continue**, and enter **THE LIBRARY OF WHISPERS**. Visit Vesper, Quill and Ember in turn, remembering the five glyphs, cipher wheel and glowing book letters. Through Crowe decode and submit the five-letter word; then use Vesper’s three timing intervals and Crowe’s three-beat lever to enter the Crypt. Walk the maze through Wren while reading the guide Lenses, then restore all three streams in Kaashi, seal your secret offering and earn the solo ending.
6. Refresh while switching Lens. The tab should reconnect to your original solo seat, keep the 25-minute countdown in progress, remember both equipped powers, and eventually show only the new Lens's clue. A different tab with the private URL but **without the secret** must not join your chamber.

## Exactly how to test multiplayer with 3 tabs

1. **Tab 1:** Open `http://localhost:8080`, click **Gather a Circle**, enter **Ada**, leave capacity at **5**, then click **Create room**. Note the four-letter room code displayed.
2. **Tab 2:** Open a **new tab**, navigate to `http://localhost:8080/room/ABCD` (replace `ABCD` with the real code). Enter **Bram** and click **Join room**.
3. **Tab 3:** Open another **new tab** to the same room URL. Enter **Clara** and join. All three tabs should list Ada, Bram and Clara, each with a green presence dot. **Do not use "Duplicate tab"**; use new tabs so each tab retains an independent seat identity.
4. **Tab 1:** Select **Medium**. **Tab 2:** Select **Archivist**. **Tab 3:** Select **Locksmith**. The server automatically merges the Lantern-bearer role into Ada's seat and Walker into Bram's seat.
5. Click **I am ready** in **each tab**. In Tab 1, click **Start the séance** (only the host can start).
6. In **every tab**, admire the dramatic role card, then click **Enter the foyer**. You should see the same 20-minute candle decreasing in sync.
7. **Tab 1:** Read the lantern scratch-mark order `✶ → ☾ → ❦ → ⚱`. **Tab 2:** Read the four randomized hour numbers corresponding to those four symbols in the diary. **Tab 3:** Use the up/down buttons on the four clock dials to enter those hours **in scratch-mark order**, then click **Turn the key**.
8. **Test a wrong answer first:** leave Tab 3's dials at `1, 1, 1, 1` and click Turn the key. Every tab should show a shake/red flash and lose 30 seconds. Wait a couple seconds between submissions.
9. **Test a hint:** In any tab, click **Reveal hint 1**, confirm the 60-second cost. All three tabs show the same hint and lose 60 seconds. There are three escalating hints in this stage.
10. Enter the correct ordered hours in Tab 3. All three tabs should hear a chime **if sound was enabled**, see a door creak open, and receive **Continue into the darkness**. Click **Continue** in any tab. All three should enter **THE LIBRARY OF WHISPERS**. Combine Vesper’s wall glyphs, Quill’s wheel, and Ember’s lit book letters. Crowe submits the decoded word. Once the lever chamber opens, all three players press and hold their levers together for three uninterrupted seconds. One release resets everyone. The server opens the bookshelf and enters **THE CRYPT OF THE HOLLOWS**; escape the traps, then continue into the Kaashi finale.
11. Optional: refresh Tab 2 during play. It must rejoin **Bram's existing seat** rather than adding a fourth player. Also try closing Tab 1: the host role migrates to the next connected player. The candle does not pause.
12. The current host can click **Enter the manor again**, returning the same party to the lobby with freshly seeded Foyer and Library solutions.

**Sound note:** Sound is **off by default**. Click **♫ Sound off** to opt in; browsers require a user interaction to enable the Web Audio API.

**Identity note:** Each tab uses `sessionStorage` to keep its seat token through normal refreshes. A closed tab, cleared site storage, private session ending, or another device may lose this token. This is intentionally different from account-based cross-device recovery.

## Test the authoritative server

Start the server on port 8765, then in another terminal:

```bash
PORT=8765 python server.py
# separate terminal:
python -m unittest discover -s tests -v
node tests/test_ui_render.cjs
```

The test suite includes `tests/test_solo.py` for a complete solo Stage 1 run and refreshing during a Lens switch, plus `tests/test_ui_render.cjs` for client render smoke tests. The complete Python suite covers default roles for 2–5 players, all combinations of primary-role choices, seed logic, expiry, and a three-player WebSocket round including correct/incorrect codes, hints, unauthorized attempts, presence, host migration, seat reconnection, late-join blocking, stage progression and replay.

## Deployment — Render FREE

`render.yaml` selects Render's **free** Python web service plan, with **no persistent disk**.
The game server keeps all room state in memory. Cold starts, restarts, redeploys and idle
spin-downs erase in-progress rooms. This is expected for this free-tier milestone.

After pushing this folder to your GitHub repository, deploy with a Render Blueprint
(`render.yaml`) or create one Python web service with:

- Plan: **Free** (no paid resources, no disk)
- Build command: `pip install -r requirements.txt`
- Start command: `python server.py`
- Health check path: `/health` (returns JSON `status: ok`)
- `PORT`: supplied automatically by Render; the server binds `0.0.0.0:$PORT`
- WebSocket: `wss://YOUR-SERVICE.onrender.com/ws`, same origin as frontend

The landing page opens a readiness WebSocket (`HELLO` → `READY`) and shows
**“Waking the spirits…”** with exponential retries until connected. It also sends
application-level `PING` messages every 25 seconds on an open WebSocket, including
while in the lobby. Connected clients keep the WebSocket active, but browser pings
cannot prevent sleep when no players have the page open, nor do they guarantee that
Render will never recycle or sleep an instance. During a cold start, the browser may
show its own loading spinner before the server can deliver the HTML page.

Do not scale the free in-memory service beyond one instance. For persistent sessions
or reliable long-lived games, use a shared data store and coordination layer later.

## Milestone boundaries and known caveats

- **Stages 1 and 2 are playable.** The candle keeps burning through the door and bookshelf reveals; only the approved Ember power may freeze time. Stage 3 is a placeholder, not full-game victory. Solo receives a separate *Library Trial* rank, not a full escape award.
- The Medium sees four unlabeled portraits with symbols as specified. Because the Archivist already knows symbols and hours, the Medium is helpful to storytelling but is not strictly necessary to solve the numerical code. The Archivist and Lantern-bearer are deliberately distributed to separate players so the puzzle cannot be solved by one seat.
- Host migration is immediate on detected disconnect. During a short transient network disruption, host privileges may shift; a returning original host keeps the same seat but does not reclaim host privileges automatically.
- Lobby Start requires **every joined player** to click Ready, in addition to the host pressing Start; at least two must be connected.
- Memory-only rooms are lost on free-service spin-down, restart, and redeployment. Existing seat tokens cannot recover an erased room.
- Room code guessing is rate-limited per IP, but this is a casual game rather than high-security infrastructure. Add stronger admission protections before large public promotion.
- Automated WebSocket rules tests are included. Browser screenshots and cross-device audio/animation testing must be performed from a normal browser because the build environment's Chromium disallows navigation.

## Project structure

- `server.py`: authoritative in-memory circle + solo server, per-seat clue projections, Lens gate, cipher/lever state, and rhythm timing
- `static/index.html`: document and fonts
- `static/styles.css`: original CSS/SVG-inspired cinematic art, layout, responsive animations
- `static/app.js`: UI rendering, WebSocket client, candle animation, opt-in Web Audio
- `tests/`: game rules, multiplayer and solo full-library completion, reconnect recovery, and JavaScript UI smoke tests
- `requirements.txt`: Python dependency
- `render.yaml`: hosting blueprint

## Stage 2 — THE LIBRARY OF WHISPERS

After the Foyer door opens, press **Continue**. Stage 2 immediately begins with a fresh set of three escalating hints (each costs 60 seconds); the candle is *not* reset or paused.

**Decode:** Vesper sees five ghost glyphs in order; Quill sees the seeded mapping between glyphs and letters; Ember sees five illuminated books with the answer letters shuffled among dark decoys. Only Crowe has the binding word field. The correct answer is one of ten distinct-letter five-character spooky words, chosen and encoded from the server's round seed. Invalid format is rejected without penalty; an incorrect valid word costs 30 seconds.

**Circle levers:** Once the cipher succeeds, every occupied seat has a brass lever. Press and hold with a mouse button or touch (keyboard Space/Enter also supported). All screens show live hold status. Every hand must stay down for three full seconds measured by the server. Releasing or disconnecting cancels everyone's progress. The bookshelf opens after authoritative completion.

**Solo lever:** Visit Vesper's Lens and memorize the three cadence intervals (seconds). Return to Crowe (each switch takes two real seconds). Start the rhythm and press-hold the lever before the first beat. On each glowing beat, release and re-press promptly. Three successful beats open the shelf. You may restart a missed rhythm without an additional wrong-answer time penalty; clock time continues burning.

The cinematic elevation uses only original CSS/SVG, a heavy synthesized drum when sound is opted in, a slow zoom, drifting dust, an opening bookshelf, a light burst and title slam. Reduced-motion presentation disables nonessential animation, not timed gameplay.

**Deployment policy:** To release a future milestone, run the full Python suite and JavaScript render smoke tests, commit and push the tested source, deploy on Render Free, and verify both modes from its HTTPS origin. Render Free's in-memory rooms can disappear on instance restarts or redeployments; a 25-second heartbeat is not a guarantee of permanent availability.


## ChatGPT Sites frontend + Render server split (Milestone 2 hosting adapter)

The new `sites-frontend/` directory contains the exact original Gothic UI
with a deployment adapter: it connects to
`wss://the-last-candle.onrender.com/ws` instead of the local WebSocket path.
Site-hosted invite links are `/?room=ABCD` and solo private reconnect URLs are
`/?solo=<id>`, so deep links work without server-side route rewrites.

**The Python server remains the only authority.** It validates puzzle answers,
lever holds, role permissions, character abilities, timing and seat credentials.
Server `ALLOWED_WS_ORIGINS` controls which cross-origin browser WebSockets can
connect; only exact listed Sites origins are allowed. Set the value once the
actual Sites URL exists. The origin is not a secret or an authorization token.

For deployment steps, tests and known limitations, read `SITES_DEPLOY.md`.
Render defaults to `SERVE_FRONTEND=1` to preserve the existing working link
until Sites is verified; setting it to `0` makes Render backend-only.

## NEW — Ghost conversations and tabletop-RPG layer

**The Foyer and Library have playable ghost conversations and the story/RPG layer extends through the Crypt; the Kaashi finale is a separate ceremonial resolution.** Each stage has a resident ghost: Horace Tock in the Foyer and Prudence Page in the Library. Ghosts have role-specific server-projected replies; the speaking seat rotates, and everyone sees the same selected reply and ghost response. Solo sees replies for its current Lens, with the original two-second switch preserved. A 4-exchange conversation opens a server-authoritative crossroads choice or party vote.

- **Warmth:** 0–3 spirit flames. Kindness, questions and skill checks raise or lower warmth and reveal clues. At zero the ghost goes cold for 30 seconds and the server burns 30 seconds from the candle. A timed server task brings the ghost back at warmth 1; reconnects see the correct state.
- **Wick:** Candle spirit and narrator; original short second-person quips are shown in a distinct hand-lettered narrator box.
- **Stats and dice:** CHARM/WITS/NERVE, server-side d20 checks and shared roll outcomes. Natural 20 grants +30 seconds and a critical celebration; natural 1 gives a harmless fumble line. The client draws a chunky 1.5-second d20.
- **Help and advantage:** Multiplayer non-speakers spend their next speaking turn to give advantage; solo players may pay 30 seconds to *Steady your breath*. Dice and clocks are never client-calculated for game rules.
- **Crossroads:** After a ghost conversation, vote on the Foyer pocket watch (WATCH) or Library fine/bookmark (BOOKMARK). Majority wins; ties get server d20 roll-offs. Item inventory, flags, warmth, votes, and roll history survive refreshes.
- **Closure:** Solving the room's *original unchanged puzzle* gives the resident ghost a tender goodbye. The Crypt is playable, including Reginald’s optional story/crossroads; its puzzle leads into the playable Kaashi finale.

**Play-testing note:** Conversation and crossroads are available alongside the original puzzle actions (not forced prerequisites). This keeps the tested fast-path puzzle flow and allows speed-runner groups to solve early; those groups may miss a room's optional crossroads. This release includes a full-game win/loss ending, separate solo and multiplayer ranks, and replay.

**Design authority:** `style-preview.html` is the exact owner-approved source. `DESIGN.md` now explicitly supersedes the old cinematic/Creepster styling in favor of Patrick Hand/Nunito, flat plum/teal/navy, hand-drawn SVG, 3-seed line-boil, and hard ink shadows only.

**New automated tests:** `tests/test_story_rpg.py` checks dice, advantage, vote ties, solo checks, connected clients sharing identical outcomes, warm/cold timing, ghost closure and reconnect-persistent flags. `tests/test_story_ui.cjs` checks narrator/ghost UI, speaker controls, solo Lens reply controls and crossroads.

## Stage 3 playable — THE CRYPT OF THE HOLLOWS

The Library now leads into an authoritative, seeded 6×6 Crypt with eight traps and a guaranteed safe route. Wren alone moves via four arrows (or keyboard arrow keys). All players see Wren's position in sync. A trap costs 30 seconds and sends Wren to the entrance; Wren's **Sure Step** (if available) protects one trapped tile.

- **Vesper (SEER):** hidden traps in columns 4–6 (ghost skulls).
- **Ember (LIGHT):** hidden traps in columns 1–3.
- **Quill (KEEPER):** an inscription naming one safe tile.
- **Wren (VOYAGER):** own tile and adjacent outlines only, not the guides' ledger.
- **Two players:** non-Wren guide receives the full trap-coordinate ledger, with fog still masking distant floor outlines.
- **Solo:** switch Lenses for asymmetric trap knowledge; return to Wren to walk. The familiar two-second Lens cost and two equipped abilities apply.

The three Crypt hints retain their one-minute candle penalties. Sir Reginald's conversation, vote and possible shortcut remain optional. At the sealed exit a flat-color golden-light reveal announces **SOMETHING WAITS BEYOND.** Continue through the sealed door into Kaashi to earn the full-game ending and separate solo or team ranks.

The approved flat-color visual reference `style-preview.html` is unchanged. `crypt_engine.py` contains the private maze generator, fog filters and movement rules; `server.py` is the sole authority and the static/Sites clients only render their seat-specific state. The client sends `CRYPT_MOVE` and `CONTINUE_CRYPT`; no path or complete trap map is transmitted to Wren.

### Run all tests

```bash
python -m unittest discover -s tests -q
node tests/test_ui_render.cjs
node tests/test_story_ui.cjs
node tests/test_crypt_ui.cjs
node tests/test_sites_client.cjs
```

Upload to `Dasika-Vaishnavi/the-last-candle` **under its existing `the-last-candle/` folder**, replacing the old files; include the new `crypt_engine.py` and `tests/test_crypt.py`. Render Free auto-deploys commits to `main`. The public Render URL will not contain this four-stage release until the corresponding commit deploys successfully. The Sites frontend must be published separately through the Sites capability, with its exact origin allowed in Render.

## Stage 4 — The Kaashi Finale (four playable rooms)

After the Crypt door reveal, the game continues into **BENEATH KAASHI · THE CAVE OF THE SEVERED FLAME**. An original abstract, non-gory Goddess Chinnamasta drawing in temple gold, saffron and sindoor crimson presides over the symbolic restoration of a sacred yantra.

- **The Three Streams:** Every stream has five independently rotatable tiles on a 3×3 board, a continuous route and a receiving bowl. The server generates and validates the three routes. With 2 players, one receives two sections; with 3 players, one each; with 4–5, multiple players share sections. All three must light simultaneously. In solo, Vesper/Quill/Ember Lenses control sections 1/2/3.
- **The Offering:** Every player secretly seals one choice—an unused owned ability, 60 seconds of candle, or nothing. No choices leak to other players before everyone votes. The threshold is one meaningful sacrifice per player (one for solo). The simultaneous reveal and acceptance are decided by the server. A collective refusal costs 120 seconds, then everyone chooses again. A successful round consumes the gifts; depleted candle time causes a loss instead.
- **Victory:** Dawn returns to Hollow Manor and Eleanor finally rests. Show the server-scored remaining candle time, separate solo and group rank titles, party members, ability usage and a fun statistic. **Loss:** Show a quiet farewell and all puzzle solutions. **Play Again:** Entirely new puzzles and the character/solo-ability choice screen.
- **Original presentation:** The only Kaashi scene uses gold, saffron and sindoor crimson; earlier rooms retain the literal approved `style-preview.html` system (flat room color, Patrick Hand / Nunito, bold hand-ink SVGs and hard offset shadows). The Goddess is never depicted as a villain or with gore. Music is user-opt-in. Reduced-motion preferences disable transition animations.

### Run the Stage 4 checks

```bash
python -m unittest discover -s tests -q
node tests/test_ui_render.cjs
node tests/test_crypt_ui.cjs
node tests/test_story_ui.cjs
node tests/test_finale_ui.cjs
node tests/test_sites_client.cjs
```

The Python backend is still the authoritative runtime for all puzzle solutions, dice results, candle penalties, room state and secret offerings. `/health` remains available, the WebSocket uses `/ws`, the client pings every 25 seconds, and the Render Free service uses an ephemeral in-memory room registry (rooms are lost on instance restarts).


## Confirm the current public version

After manual upload and Render auto-deployment, visit `https://the-last-candle.onrender.com/health` and verify `"release":"stage-4-complete"` and `"chapters":4` in the JSON. If the fields are absent, Render is serving an older build. See `UPLOAD_TO_GITHUB_FIRST.md`.
