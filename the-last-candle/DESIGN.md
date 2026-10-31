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

Only Stage 1 is currently implemented. Do not invent final mechanics or answers for the remaining stages before their separate specification.

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
- Later stages with simultaneous team actions require separately approved **solo puzzle variants**, never an unsolvable one-player copy. No Library/Crypt/finale solo mechanics are authorized yet.
- Solo completion and eventual solo victories display a **separate SOLO rank vocabulary**; Stage 1 currently awards only a **Solo Foyer Trial** rank and a Stage 2 coming-soon teaser, never a false full-game escape. Multiplayer results and score vocabulary remain unchanged.
- Preserve Victorian amber / midnight / ghost-blue, Creepster headings, IM Fell English prose, original CSS/SVG silhouettes, subdued smoke and drifting embers, opt-in sound (off by default), touch-sized controls, and accessible symbol+color cues.
