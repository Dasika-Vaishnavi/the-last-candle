# THE LAST CANDLE — Approved Creative Brief

**Status:** Locked creative direction (October 31, 2026). All future milestones must follow this document. Changes require explicit user approval.

## Canonical identity and lore
- Title: **THE LAST CANDLE**. Place: **Hollow Manor, Halloween night, 1893**.
- The players' séance went wrong; Eleanor Hollow's ghost sealed the manor. The team shares one 20-minute, server-authoritative candle and must escape together.
- Eleanor's father stole a sacred **yantra** from a hidden cave shrine of **Goddess Chinnamasta** beneath **Kaashi (Varanasi)**. The theft cursed his family. Eleanor remains bound to Hollow Manor until the yantra is returned.
- **Eleanor's ghost is the haunting; Goddess Chinnamasta is the divine judge, never the villain.**

## Canonical four-stage sequence
1. **Foyer:** clock code reconstructed by asymmetric portrait, diary, lantern, and Locksmith clues.
2. **Library:** cipher and simultaneous levers.
3. **Crypt:** blind maze; Walker moves while the others guide.
4. **FINALE:** crypt opens into a **vision of the Chinnamasta cave beneath Kaashi**; the yantra is returned to end the curse. This is the **only Kaashi / Indian scene** in the entire game. Do not add an Indian scene or temple backdrop to earlier stages.

Stages 1 and 2 are implemented. Do not invent Stage 3 or finale mechanics or answers before their separate specifications.

## Cinematic language
The owner asks for an epic, grand-scale cinematic energy associated with S. S. Rajamouli: imposing architecture photographed from low angles, embers and ash, mythic sense of scale, and breathtaking elevation moments. Express these **broad aesthetic qualities through original work**, not copied shots, storyboards, melodies, marks, actors, or assets.

Each successful stage solve gets an **elevation moment:** slow zoom → original heavy drum hit when audio is enabled → light burst → oversized title slam. The finale is the largest and most epic sequence.

## Atmospheric motion
Ethereal séance: translucent ghosts slipping through incense/candle smoke, soft bloom from lights, floating embers and dust, restrained 2.5D parallax, slow elegant reveals. **No cheap jump scares.** Effects remain performant and never obscure clues.

## Visual language
- Manor palette: candlelight amber, midnight black, ghost blue.
- Finale palette shifts to temple gold, saffron, sindoor crimson.
- Creepster for large titles only; IM Fell English for readable body text, with legible fallback fonts.
- Original CSS and SVG artwork only; no copyrighted images, film titles/logos/posters/music, character designs, game logos, recognizable proprietary UI assets, or actor likenesses.
- For the future lobby: a **high-polish, original tactical-character-selection experience**, using the owner's “Valorant-style” reference as a functional inspiration only. **Await the next lobby specification before building.**

## Respectful depiction of Goddess Chinnamasta
A reverent, **abstract radiant silhouette** within a glowing lotus-yantra; **three crimson-gold streams of light**, **no gore**. Never present the goddess as evil, a cheap scare, or the monster. The divine presence judges the restoration; Eleanor is the ghost haunting the manor.

## Gameplay and technology guardrails
- 2–5 players; no login, no install, four-letter room codes; lobby-only new joining and same-seat reconnect.
- Client sends actions; server exclusively owns roles, clues, answers, timer, penalties, stage progression and authoritative state.
- Candle never pauses. Wrong valid answers −30 seconds; any of three stage hints −60 seconds each, visible to everyone.
- The team cooperates through external conversation plus a compact in-game spirit-board text fallback.
- Host creates and starts the room; hostship migrates when the host disconnects.
- Each role card clearly says **WHAT YOU CAN SEE** and **WHAT YOU MUST DO**; private information is split so at least two players are needed.
- Mobile-first portrait, responsive touch targets, readable contrast, symbol+color for essential clues, optional synthesized sound **off by default**, respect `prefers-reduced-motion`.
- **Target:** smooth 60fps on mid-range phones; optimize CSS transforms, SVG, effects and network updates; do not claim 60fps without device testing.

## Delivery discipline
Preserve the current Milestone 1 experience during deployment. The next user request will define lobby visual details. Later implementations must refer to this design file; the user approves stage specifications one at a time.

## Approved character-selection extension — Milestone 1.1
**This section supersedes the prior instruction to await lobby details.** The five-character roster and interaction below are approved as the canonical character-select system. It uses an original gothic-seance interpretation of a tactical hero-select screen: do not reuse any proprietary interface, actor, illustration, logo, or character assets.

- **Five tall, original CSS/SVG silhouette portrait cards**, each with its own glyph, color and class tag. Tapping previews what that character sees and their server-validated, once-per-game ability.
- A player presses **LOCK IN** to claim one primary character; only one player may lock each character. Locked cards display the current player's name live. Every screen receives a dramatic, original cast/lock animation and an original synthesized drum hit when sound is enabled.
- **45-second server-timed selection**, beginning when the second player joins the lobby. Unlocked players are automatically assigned an unclaimed character at expiration. Players who join afterward but before Start are assigned an unclaimed character immediately. The host can Start early once 2–5 seated players have locked in and declared ready.
- **Merging** distributes all five gameplay roles among 2–4 players. A player explicitly sees **“You also carry: …”** once the existing seats are all locked. Each merged role carries its own ability, and each ability can be used only once per round, enforced by the server.
- **Team composition bar** appears at the bottom of the selection interface.

| Character | Role | Class | Once-per-round ability | Scope |
|---|---|---|---|---|
| VESPER | Medium | SEER | **Veil Sight**: one extra hidden Foyer clue to all players for 10 seconds | Stage 1 supported |
| QUILL | Archivist | KEEPER | **Remembered Page**: reveal next normal hint at zero candle cost | Stage 1 supported; uses one of 3 hints |
| EMBER | Lantern-bearer | LIGHT | **Steady Flame**: freeze remaining candle time for exactly 20 seconds | Stage 1 supported |
| CROWE | Locksmith | BINDER | **Second Turn**: arm one protection so the next wrong clock-code submission costs no time | Stage 1 supported |
| WREN | Walker | VOYAGER | **Sure Step**: safely pass one crypt trap tile | Reserved for Stage 3; no Foyer trap tiles exist |

**Explicit timer-rule exception:** The owner's new Steady Flame mechanic intentionally overrides the earlier blanket "never pauses" rule once per round. The server alone schedules the 20-second freeze and deadline extension. Ordinary network loss, role reveals, hints, or stage transitions do not pause the candle. Any penalties applied while frozen still deduct time exactly once.

**Scope restraint:** Stage 1 remains the Foyer. Wren's Stage 3 ability is displayed for clarity but cannot yet be cast; do not invent Stage 3 puzzle logic before approved specs arrive.

## Approved SOLO VIGIL extension — Milestone 1.2
**This section authorizes an additional mode; it does not change multiplayer rules, balance, role merging, or canonical story.** The player's latest explicit solo specification governs the exceptions below.

- The landing page offers **GATHER A CIRCLE** (existing multiplayer flow) and **ENTER ALONE** (no invite code). The existing join-with-code entry remains available for groups.
- A solo chamber is server-created, private, and has **exactly one anonymous seat**, recovered after refresh with the same secret seat credential. Other players cannot join it, even if they know its internal room identifier.
- The solo candle begins at **25 minutes**, compared with 20 minutes for a multiplayer circle. Time and penalties remain server-authoritative. The approved Ember / Steady Flame exception still freezes the clock for 20 seconds if this is one of the two equipped solo abilities; otherwise no pauses.
- The player **carries all five character responsibilities** but may inspect the private clue of **only one active Lens** at a time. The Lens bar stays at the bottom of Stage 1 and shows original SVG portraits for **VESPER / QUILL / EMBER / CROWE / WREN**.
- Switching Lens invokes a server-authoritative **2-second** transition. A smoke-wipe animation obscures clues; the server withholds *both* old and new clues until the transition finishes. Candle time continues to burn. Reduce motion visually when requested without removing the two-second gameplay cost.
- Before lighting the candle, the player equips **exactly two** of the five character abilities for that round. They can use only those two powers, only while the corresponding Lens is active. Equipping an ability is separate from obtaining that character's clue. Wren's **Sure Step** remains explicitly Stage-3-only; never invent a Stage-1 substitute.
- **The Foyer** is played by visiting each Lens, mentally combining the diary hours and scratch-mark order, and using **CROWE's Lens** to set the four dials. Penalties, hints, seeded puzzles, cinematics and audio settings continue using the existing engine.
- Stages with simultaneous team actions require separately approved **solo puzzle variants**, never an unsolvable one-player copy. Stage 2 Library now has an approved solo rhythm variant; Crypt and finale solo mechanics remain unspecified.
- Solo completion and eventual solo victories display a **separate SOLO rank vocabulary**. After the completed Library, solo now awards only a **Solo Library Trial** rank and a Stage 3 coming-soon teaser, never a false full-game escape. Multiplayer results and score vocabulary remain unchanged.
- Preserve Victorian amber / midnight / ghost-blue, Creepster headings, IM Fell English prose, original CSS/SVG silhouettes, subdued smoke and drifting embers, opt-in sound (off by default), touch-sized controls, and accessible symbol+color cues.

## Approved THE LIBRARY OF WHISPERS extension — Milestone 2
**User-approved October 31, 2026.** Only Stage 2's cipher and levers are implemented; Stage 3 remains a placeholder.

- Setting remains Hollow Manor; there is no Kaashi/temple scene in the Library. The opening title card reads **THE LIBRARY OF WHISPERS**. Story: “Books rearrange themselves. A voice hisses a word you cannot quite hear.”
- **Part A: the cipher.** Vesper alone sees the five ghost-written symbols in order. Quill alone sees the torn wheel translating symbols to letters, freshly seeded each round. Ember alone identifies five letters on glowing book spines amid unlit decoys; those letters verify the intended five-letter word. Crowe alone types and submits the answer, which the server validates against a seeded word list. Valid incorrect words deduct 30 seconds; three escalating Library hints each cost 60 seconds. Quill’s previously authorized free-hint power can reveal the next Library hint if still unused.
- **Part B: levers, multiplayer.** Every seated player holds their own lever simultaneously for **3 uninterrupted server-measured seconds**, through touch, mouse or keyboard. Everyone sees all lever states live. One release or disconnect resets all holds; the server is the only judge of completion.
- **Part B: SOLO.** The player may look through one of the five Lenses at a time, with the existing 2-second server-enforced smoke transition. Vesper’s Lens reveals a three-beat cadence. Only Crowe operates the solo lever: press and hold, release on each server-scheduled glowing beat, and promptly re-press for the next beat. Missing a beat restarts the ritual, without an extra 30-second code penalty. The player still equips only two once-per-round abilities.
- **Success elevation:** original light burst, ash/embers, animated bookshelf opening, slow zoom, heavy synthesized drum hit when audio is enabled, and oversized title slam. Cinematic scale is inspired by broad epic-film techniques; no direct replication of any filmmaker’s shots, music or visual trademarks. Provide reduced-motion rendering without bypassing gameplay timing.
- **Next:** The group advances to a Stage 3 placeholder labeled **THE CRYPT AWAITS**. Solo receives a separately labeled Stage 2 trial rank, never a false game victory.
- Candle remains server-authoritative and burns across stage transitions; Ember's explicitly approved 20-second power is the only gameplay freeze. Active rooms remain in memory for this free-tier version and can be lost on instance restarts.

## APPROVED VISUAL SYSTEM — OVERRIDES ALL PRIOR VISUAL DIRECTION

**Newest owner direction; highest priority for UI implementation.** The literal `style-preview.html` in this repository is the approved visual reference, copied without modifications from `style-preview (1).html`. Earlier notes about Creepster, IM Fell English, gradients, textures, cinematic haze, floating embers, particles, realistic lighting, glowing doors, parallax or wax seals are **superseded**.

- Background: **one flat color per room**, Foyer dusty plum `#6B4E71` / cream `#F4E9D8`, Library teal `#2F6F73` / mustard `#E3B23C`, Crypt navy `#1F2A44` / bone `#EDE6D6`.
- Accents: ink `#1A1A1A`, paper `#FFF8EC`, coral `#E8735A`, blush `#F2A7A0`.
- Fonts: **Patrick Hand** for titles, story, and speech; **Nunito** for tiny UI labels. Original SVG character art uses 5–6px uneven outlines, flat shapes, dot eyes, optional blush, and brow/mouth expression variants.
- **Three-seed line boil:** SVG fractal turbulence + displacement, seeds `[3,17,42]`, change every **140ms**. Disable for `prefers-reduced-motion: reduce`.
- Buttons, character cards, pills, narrator cards, dice, and dialogue bubbles use rounded rectangles, 3–5px ink borders, **hard offset shadows**. No blur, grain, mist, particles, gradients, bloom, glows, wax seals, or copyrighted visual assets.
- Motion uses line-boil, bobbing, pendulum swings, chunky frame-by-frame d20 tumble, a simple SVG ghost confetti treatment for criticals, and straightforward position-based goodbye drift. No atmospheric graphical effects.

## Ghost conversations + tabletop-RPG systems — newly approved

Resident ghosts have short original 4-exchange conversations with role-specific replies, synchronized authoritative turns, 3-flame warmth, clue fragments unlocked at warmth thresholds, 30-second cold periods with a **30-second candle penalty**, and a tender closure when the room puzzle is solved.

- **Foyer:** Horace Tock, anxious clockmaker, deceased 1871. His sadness about stopping the great clock after the Hollow deaths underpins clue fragments. A correct clock-code submission triggers the clock restarting and Horace's farewell.
- **Library:** Prudence Page, grieving librarian, awaiting a final letter's reader. Her clues point toward ghost symbols, glowing book spines, and a synchronized lever hold. When the Library is solved she can let the book go.
- **Crypt:** Sir Reginald Rattle, misguided knight, with the offered shortcut and compass story states. **The actual Crypt maze remains unimplemented; these are approved data/rules only.**
- **Finale:** Eleanor remains the haunting as previously canonized, with a conversational framework reserved. The Chinnamasta cave/yantra finale is not implemented or changed.

**Wick, the candle spirit** narrates in second person with dry, kind humor in a distinct, hand-lettered box. The narrator reacts to dialogue, dice, crossroads and closure. Do not substitute client-created outcomes.

### RPG character stats

| Character | CHARM | WITS | NERVE |
|---|---:|---:|---:|
| Vesper | +2 | +0 | +1 |
| Quill | +1 | +2 | +0 |
| Ember | +0 | +1 | +2 |
| Crowe | +0 | +2 | +1 |
| Wren | +1 | +0 | +2 |

The server decides all d20 rolls, advantage, modifiers, difficulty class checks, critical (natural 20) and fumble (natural 1), and broadcasts the same result and timestamp to every client. Natural 20 grants +30 seconds of candle time and a critical moment; natural 1 produces a harmless narrated fumble. Solo uses the active Lens character's stats. In multiplayer a non-speaker may use **HELP** to grant advantage, spending their next speaking turn; in solo **Steady your breath** costs 30 seconds for advantage. Cap is **four checks per room**; narrative skill checks reserve capacity for the crossroads. The 1.5-second chunky line-art d20 animation changes no server result.

**Conversation stage:** player-specific replies may be plain or tagged `[CHARM 12]`, `[WITS 12]`, etc. Every player sees the shared latest reply, ghost expression, turn indicator and warmth; only the active speaker may choose. Solo options change with the active Lens, which still takes two seconds to switch. Four exchanges unlock the room crossroads. Conversations do not change Foyer cipher, Library puzzle, or lever algorithms.

**Crossroads:** after dialogue, multiplayer seats vote; strict majority resolves early or, after every connected seat votes, a tie is resolved by server-drawn d20s. Solo chooses alone. Server tracks WATCH, BOOKMARK, COMPASS, WRONG_TURN, criticals, fumbles, votes, warmth, cold state, dialogue history, and candle time. Foyer choices: pry the watch `[WITS 13]` (success WATCH, ordinary failure −30 seconds/warmth −1) or leave it (warmth +1 and a free hint). Library choices: pay 30 seconds (warmth +2), argue `[CHARM 14]`, sneak `[NERVE 13]` (success BOOKMARK, ordinary failure Prudence goes cold). Crypt future rules: trust Reginald `[NERVE 15]` (success shortcut + COMPASS, failure trap + WRONG_TURN) or map carefully. Full crypt navigation and final ending selection await later stage specifications.

**Availability:** Stage 1 and Stage 2 conversation, dice, vote and closure systems are playable. Crypt/Finale story objects are implemented as future-stage rules but not exposed as playable stage content yet. Existing tests, reset/replay, room membership, anonymous seat reconnection, role/ability constraints and server-authoritative timer remain mandatory.

## APPROVED STAGE 3 — THE CRYPT OF THE HOLLOWS

**User-approved October 31, 2026. This section supersedes all earlier statements that the Crypt is merely a placeholder or that Stage 3 remains unspecified.** It also supersedes the older Stage 2 trial endpoint: the Library continues directly into a playable Crypt and solo scores are awarded at the end of the Crypt trial. The approved `style-preview.html` remains the authoritative visual reference and no gradients, glow, grain, mist, particles, blur or wax seals may be added.

- **Title card:** `THE CRYPT OF THE HOLLOWS`; introduction: “The candle flickers. The crypt floor is a grid of ancient tiles, and some of them are traps.” Location is still *Hollow Manor*, not Kaashi or the finale cave.
- **Maze:** a server-seeded, exactly six-by-six grid, with the entrance at row 6, column 1 (south-west) and the sealed exit at row 1, column 6 (north-east). Every round samples eight trap cells outside one guaranteed connected path. The server owns the full trap map and Wren's current tile; clients receive only seat-appropriate information.
- **Wren / VOYAGER:** Wren's player alone moves with large touch-sized cardinal arrow buttons (and keyboard arrow keys). Their map has heavy fog: only Wren's tile and its up/down/left/right neighbors have visible outlines. Everyone sees Wren's authoritative position update live. Entering a trap causes an original skeletal-hand line-art animation, deducts thirty real seconds and moves Wren back to the entrance.
- **Sure Step:** Wren's approved once-per-round power can be armed during Stage 3 and safely crosses the next trapped tile one time. It does not modify the trap layout, undo earlier trap penalties, or become usable in the earlier rooms. Solo players must equip it among their two chosen powers before play.
- **Asymmetric guides:** Ember/LIGHT sees the trap coordinates in columns 1–3 (left half); Vesper/SEER sees columns 4–6 (right half), represented by simple hand-drawn skulls; Quill/KEEPER reads an inscription naming exactly one guaranteed safe tile. The player's unique view also has fog limited to Wren's vicinity; known trap coordinates can appear in an otherwise hidden ledger. The Wren-moving seat cannot view guide trap coordinates even when it also carries merged roles.
- **Two-player exception:** the non-Wren guide sees all eight traps on their private ledger, but distant grid-cell outlines remain hidden until Wren approaches. This ensures the combined role assignments are solvable with two participants.
- **Solo:** The player controls movement only through Wren's Lens. Ember's Lens shows left-half trap knowledge and Vesper's Lens right-half knowledge; Quill can read the safe-tile inscription. The existing **two-second server-enforced Lens switch** still withholds clues during transition, and the candle keeps burning.
- **Hints:** three escalating, shared Crypt hints deduct one minute each. Quill's existing free-hint power is still available if equipped/assigned and unused. Existing Ghost + RPG conversation system features Sir Reginald Rattle and an optional crossroads; a successful NERVE shortcut may skip roughly half the guaranteed path, while a failure charges the approved penalty and secret `WRONG_TURN` flag. The underlying maze remains walkable whether or not the party converses.
- **Crypt completion:** crossing the exit tile gives Sir Reginald closure, freezes no gameplay timer, and shows an original flat mustard-on-navy sealed-door reveal: slow scale, chunky title slam **`SOMETHING WAITS BEYOND.`** and a mysterious golden color field from the other side. After the reveal, proceed to a **Stage 4 placeholder**, not an invented finale. In solo, award a separately labeled Solo Crypt Trial rank only after the Crypt is complete.
- **Delivery and testing:** preserve lobby, Foyer and Library flows, 20-minute multiplayer/25-minute solo timers, per-player WebSocket state, reconnect/seat credentials, heartbeat, no disk, and no paid Render services. Run all legacy and new multiplayer/solo Crypt tests before releasing. Keep the actual Sites origin in `ALLOWED_WS_ORIGINS` once published; do not assume one.

## APPROVED STAGE 4 — BENEATH KAASHI · THE CAVE OF THE SEVERED FLAME

**Owner-approved finale, October 31, 2026. This is the ONLY Kaashi scene.** This section supersedes every older statement that Stage 4 is a placeholder or that a solo Crypt Trial is the game's final rank. There are now four playable chapters: Foyer, Library, Crypt, and Kaashi. Keep every earlier room, character card, and Ghost + RPG screen anchored to the approved byte-for-byte `style-preview.html`—the same Patrick Hand/Nunito, wobbly 5–6px strokes, `[3, 17, 42]` 140ms line-boil, flat Foyer/Library/Crypt colors and hard offset ink shadows. The Kaashi finale alone receives a purposeful temple-gold, saffron and sindoor-crimson palette and symbolic light/shrine elevation; it does not alter the manor scenes. All illustrations are new CSS/SVG drawings; no realistic gore or external sacred imagery. The Goddess is reverently presented as a majestic, abstract, non-gory divine judge, never a villain.

**Transition and story.** After crossing the Crypt exit and its 2.9-second sealed-door reveal, `CONTINUE_CRYPT` now enters real Stage 4. The manor symbolically falls away, with a light-filled title slam **“BENEATH KAASHI · THE CAVE OF THE SEVERED FLAME.”** Original, opt-in percussive audio swells. Intro text: “Eleanor's father took what was never his: a sacred yantra from this shrine. The Goddess has waited a hundred years. Return it, and give something of yourselves.” The Goddess's illustrated lotus-yantra/orb displays three *abstract light streams* in red-gold, not blood or violence.

**Part A — Three Streams.** Exactly three sacred streams, each a 3×3 grid with a randomized five-tile path from centre-facing lower entry to upper bowl. Every turn rotates one server-owned tile clockwise by 90°; the server independently checks that both ports of every route tile connect through to the bowl. Each player can only operate and see their assigned stream sections; all screens receive only the three connection indicators for unowned sections. With two players, one controls streams 1 and 3, the other stream 2. With three players, each gets one stream. Four- and five-player parties share assigned streams (index modulo three), letting every player participate. All three must remain connected simultaneously; changing a lit section can disconnect it until restored. The stage progresses only when the server has validated all three. No entire route or target orientations are disclosed in STATE.

**Solo:** Vesper's Lens controls stream 1, Quill's Lens stream 2, Ember's Lens stream 3. Wren and Crowe cannot rotate tiles. During the existing 2-second Lens switch, no tile is accessible. The candle continues burning; the 25-minute solo duration is unchanged.

**Part B — The Offering.** After restoration, each player secretly seals exactly one choice: an eligible unused ability belonging to their seat, 60 seconds of shared candle, or nothing. Solo may offer only one of the two previously equipped and still-unused abilities; the offering threshold is 1. Multiplayer threshold equals current party size (2–5). An unused ability or 60 seconds each contributes one; nothing contributes zero. The UI explains these options and costs before submission. All seats must submit before any choices become public; then all screens receive the same server-owned reveal, staggered over ~4.2 seconds. On success, selected powers become permanently spent and candle deductions apply; if there is still positive time, the party wins. On failure, neither ability sacrifices nor individual 60-second costs are consumed, but the shared candle loses 120 seconds; the attempt counter increments and everyone may seal new choices. If a cost/penalty empties the candle, the authoritative loss takes priority. Sealed choices remain secret on other screens through refreshes.

**Victory.** The restored yantra returns to its shrine in a slow-motion original SVG title moment, then cut to Hollow Manor at dawn; Eleanor's portrait drifts away with a tender line about carrying loss forward. The server fixes the score as full-game seconds remaining, with a separately labeled solo ranking and multiplayer ranking. Show the participating character cards, used/sacrificed powers, and an original fun stat (Crypt trap hits). Existing story flags (items, criticals, fumbles, votes, hidden `WRONG_TURN`) remain authoritative. The candle never resets between stages.

**Loss.** At any active chapter, the candle ending triggers an authoritative `lost` phase and Eleanor's quiet whisper. All solved and unsolved clues are revealed only in a final loss STATE: Foyer clock hours and symbol order; Library answer word; Crypt safe path and trap coordinates; Kaashi route geometry and target tile orientations. No solution or secret offering is sent early.

**Replay.** Host “Play Again” moves multiplayer to fresh character selection and solo back to the two-ability equip screen. The Foyer, Library, Crypt and Kaashi puzzles all regenerate from a new seed; timers, hints, used abilities, offerings, counters and story flags reset atomically. The browser never authorizes victory, score, offering totals, private state or a clock penalty.

**Tests and hosting.** `tests/test_finale.py` covers random generation, tile connectivity, ownership for 1–5 players, unauthorized actions, sealed offerings, a failed and successful attempt, role/Lens switching, full four-stage multiplayer and solo wins, reconnecting during a solo offering, loss solution reveal and replay. `tests/test_finale_ui.cjs` checks every new display phase and matching Sites source. Keep `ALLOWED_WS_ORIGINS` restricted to the actual published Sites origin; no Sites host has yet been issued. Render Free stays a single ephemeral, no-disk Python WebSocket backend. Do not claim a public Stage 4 version until both GitHub source and Render deployment are verified.
