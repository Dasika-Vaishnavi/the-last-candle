# Publish THE LAST CANDLE to Render Free

The source code is ready for a single free Render Python web service. No persistent disk, database, credit card, or paid Starter service is configured.

## 1. Create a new GitHub repository

In GitHub, create an **empty** repository named `the-last-candle` (do not generate a README or .gitignore because those files are already in this project). From the unzipped project folder:

```bash
git init -b main
git add .
git commit -m "Milestone 2: Library cipher and levers for multiplayer and solo"
git remote add origin https://github.com/YOUR_USERNAME/the-last-candle.git
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username. Authenticate using the GitHub browser or approved credential manager when prompted; never paste access tokens into chats.

## 2. Create the Render web service

Go to https://dashboard.render.com/web/new, select the new GitHub repository, and use:

| Field | Value |
|---|---|
| Language/runtime | Python |
| Branch | `main` |
| Plan | **Free** |
| Build command | `pip install -r requirements.txt` |
| Start command | `python server.py` |
| Health check | `/health` |
| Persistent disk | **None** |

Or import the included `render.yaml` as a Blueprint; it has `plan: free` and **no disk**. The server listens on Render's injected `PORT`.

## 3. Verify the deployed site

After Render reports a healthy deploy, open `https://YOUR-SERVICE.onrender.com/health`. It should return JSON similar to `{"status":"ok","rooms":0}`.

Open the root HTTPS URL on **two separate devices or private browser profiles**. Create a two-player room on the first, join with the four-letter code on the second, confirm both names and green presence dots, select roles, mark Ready, and start the Foyer. Check that the two countdowns agree and the Locksmith can submit the code.

## Free-tier limitations

- Render can spin down idle free services. The initial HTTP request may not show the themed loading UI until the server wakes; the UI then auto-retries WebSocket handshakes and shows **Waking the spirits…** when necessary.
- The client sends a WebSocket `PING` every 25 seconds **while the page is open and connected**. It cannot protect a room if Render stops or restarts the process, or if everyone closes the page.
- Room state and seat credentials are in the server's memory only. Restart/spin-down/deploy wipes all existing rooms. Run only one instance; multi-instance scaling requires Redis/shared state.
