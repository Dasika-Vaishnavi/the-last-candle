# the-last-candle

A minimal browser game prototype built for the ChatGPT game dev challenge.

## Game loop

- You start with a full flame and 60 seconds until dawn.
- The flame decays every second.
- Press **Stoke Flame** to restore some flame.
- Survive until the timer reaches 0 to win.

## Run locally

From `/home/runner/work/the-last-candle/the-last-candle`:

```bash
python -m http.server 8000
```

Then open `http://localhost:8000` in your browser.
