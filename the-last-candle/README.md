# THE LAST CANDLE — Milestone 1.2 (Circle + Solo)

A playable, server-authoritative Victorian horror escape-room demo for **2–5 players together or one player alone**. **No accounts. No install for players. Original CSS/SVG art.**

## Included

### Solo — Enter Alone

- Landing offers **Gather a Circle** for the unchanged multiplayer flow, **Enter Alone** for a private single-seat chamber, and a smaller link to join an existing circle.
- Solo is created immediately with no lobby invite code or share action. An anonymous secret in the tab's `sessionStorage` restores the same solo seat on refresh (`/solo/<private-id>`). Other browsers cannot join a solo room.
- Solo prep shows Vesper, Quill, Ember, Crowe and Wren's original Gothic portraits. **Choose exactly two once-per-round abilities**; every character's information remains available through their Lens regardless of which abilities were equipped. Wren's ability is for Stage 3 and cannot be used during the Foyer.
- **25-minute solo candle**, validated by the same server timer and penalties as the 20-minute multiplayer candle.
- A five-portrait **Lens switcher** stays at the bottom of solo gameplay. The client sees only the active character's clues. Switching Lens takes **two real seconds** and triggers an original smoke wipe; the server gates clue disclosure and action permissions until the switch finishes. The candle keeps burning during the switch unless an equipped Ember power is actively freezing time.
- Use **Quill** for diary hours, **Ember** for symbol order, and **Crowe** to submit the clock code. Hints and incorrect-code penalties work the same as the team mode.
- Solo Stage 1 completion shows **a separate Solo Foyer Trial rank** with seconds remaining, then Stage 2 coming soon. It is not a full-game win; future Library/Crypt/Finale puzzles await separate solo specifications.
- `TRY_AGAIN` returns to solo ability selection with a new seeded puzzle. Nothing in this mode changes multiplayer role locks or gameplay.

### Multiplayer — Gather a Circle (unchanged)

- Mobile-first Gothic landing screen (Creepster titles, IM Fell English body)
- Four-letter lobby codes, capacity 2–5, role selection, ready states, live presence, invite links and host migration
- Anonymous seat recovery across refreshes and temporary disconnections using a per-tab `sessionStorage` credential
- Assigned/mixed role reveal cards, with private role-specific Foyer clues and clear "What you can see / What you must do" instructions
- Server-authoritative 20-minute never-pausing candle, versioned synchronized state, clock dials, server-checked code, and atomic −30-second wrong-answer penalties
- Three escalating, public 60-second hints (requested by any player; no voting)
- Foyer completion with synchronized chime and animated opening door; Stage 2 coming-soon screen
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
5. Try a wrong combination to check the −30-second penalty; reveal a hint to check −60 seconds. Solve the puzzle, wait for the door to open, click **Continue**, and see a **Solo Foyer Trial** rank and Stage 2 coming-soon notice.
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
10. Enter the correct ordered hours in Tab 3. All three tabs should hear a chime **if sound was enabled**, see a door creak open, and receive **Continue into the darkness**. Click **Continue** in any tab. All three should land on **Stage 2 coming soon**.
11. Optional: refresh Tab 2 during play. It must rejoin **Bram's existing seat** rather than adding a fourth player. Also try closing Tab 1: the host role migrates to the next connected player. The candle does not pause.
12. The current host can click **Try the Foyer again**, returning the same party to the lobby with a fresh randomized solution.

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

- **Only the Foyer exists.** Successful completion freezes the milestone demonstration timer at the end of Stage 1 and shows a Stage 2 teaser; this is not the full-game victory. Solo receives a separately labeled *Foyer Trial* rank, not a full escape award.
- The Medium sees four unlabeled portraits with symbols as specified. Because the Archivist already knows symbols and hours, the Medium is helpful to storytelling but is not strictly necessary to solve the numerical code. The Archivist and Lantern-bearer are deliberately distributed to separate players so the puzzle cannot be solved by one seat.
- Host migration is immediate on detected disconnect. During a short transient network disruption, host privileges may shift; a returning original host keeps the same seat but does not reclaim host privileges automatically.
- Lobby Start requires **every joined player** to click Ready, in addition to the host pressing Start; at least two must be connected.
- Memory-only rooms are lost on free-service spin-down, restart, and redeployment. Existing seat tokens cannot recover an erased room.
- Room code guessing is rate-limited per IP, but this is a casual game rather than high-security infrastructure. Add stronger admission protections before large public promotion.
- Automated WebSocket rules tests are included. Browser screenshots and cross-device audio/animation testing must be performed from a normal browser because the build environment's Chromium disallows navigation.

## Project structure

- `server.py`: authoritative in-memory circle + solo server, per-seat clue projections and Lens gate
- `static/index.html`: document and fonts
- `static/styles.css`: original CSS/SVG-inspired cinematic art, layout, responsive animations
- `static/app.js`: UI rendering, WebSocket client, candle animation, opt-in Web Audio
- `tests/`: game rules, multiplayer, solo recovery/full-Foyer protocol tests, and JavaScript UI smoke tests
- `requirements.txt`: Python dependency
- `render.yaml`: hosting blueprint
