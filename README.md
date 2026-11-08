# Learning Path Generator

Describe what you want to learn, how much time you have per day, and for how long.
The app asks a free model on [OpenRouter](https://openrouter.ai) for a day-by-day
study plan, validates it, and shows it as an interactive checklist.

Plans, progress, and your API settings are saved locally, so a refresh does not lose
your work.

---

## Highlights

- **Day-by-day roadmap** with concepts, takeaways, practice, assignments, and revision questions.
- **In-app YouTube player** — video resources show a thumbnail; click **Watch here** to play
  them without leaving the app.
- **Saved settings** — the OpenRouter API key and chosen model are written to `.env` and
  restored on the next launch.
- **Local persistence** — plans and checkboxes live in a small SQLite database.
- **Optional MCP** — search real YouTube links and export through Google Drive.
- **Honest output** — truncation, day-count mismatches, and unverified links are flagged
  instead of hidden.

---

## What it actually does

| Step | Detail |
| :--- | :--- |
| Input | A Pydantic model validates level, format, duration (max 30 days) and daily time per unit. |
| Generation | One OpenRouter chat request returns a JSON object. Malformed or truncated output is repaired once. |
| Validation | `LearningRoadmap` validates the JSON and renumbers days so keys can never collide. |
| MCP (optional) | A YouTube MCP server is used to search real links. Only returned URLs get a "verified" label. |
| Player | YouTube video resources show a static thumbnail; **Watch here** loads an embedded player inside the app. |
| Storage | Plans and checkboxes live in `data/app.db`. |
| Export | Markdown, JSON, or an upload through a Google Drive MCP server. |

**Honest limits:** free models are rate-limited and sometimes return broken JSON.
Links without a "verified" label are model suggestions, not checked facts.
Plans are capped at 30 days; longer requests are shortened and flagged on screen.

---

## In-app videos

Resources that point to a real YouTube video (`watch?v=`, `youtu.be`, `/shorts`,
`/live`, or `/embed`) render as a card with:

- the 16:9 video thumbnail,
- title, channel, platform, and the "MCP verified" label when applicable,
- **Watch here** and the relevance note.

Clicking **Watch here** swaps the card for the official YouTube player inside that day's
expander. Only one player is loaded at a time, so long plans stay fast. Videos whose
owner disabled embedding still show **Open on YouTube** as a fallback.

YouTube **search** links, channel pages, and playlists cannot be embedded, so those stay
as ordinary links. Real playable links come mainly from the optional YouTube MCP search,
which runs for up to the first 8 days of a plan.

---

## Project structure

```
app.py                  # entry point
dashboard.py            # page setup, sidebar, navigation, routing
config.py               # environment, paths, .env settings writer
models.py               # Pydantic schemas and validation
ai_generator.py         # OpenRouter request, JSON repair, validation
openrouter_models.py    # live catalog of free models
mcp_client.py           # MCP health checks, YouTube search, Drive upload
exporter.py             # Markdown / JSON / Drive export
storage.py              # SQLite persistence
youtube.py              # YouTube link parsing, thumbnails, watch URLs
ui/
  theme.py              # CSS and small render helpers
  state.py              # session state and navigation
  demo_data.py          # loads assets/demo_roadmap.json
  views/
    generate.py         # the request form
    roadmap.py          # the active plan, player and exports
    library.py          # saved plans
    connections.py      # MCP health checks
    about.py            # how it works
assets/demo_roadmap.json
tests/
```

---

## Setup

Requires Python 3.10+.

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Copying the example environment file is optional — the app creates `.env` when you save a
key in the sidebar:

```powershell
copy .env.example .env   # optional; lets you set values before first launch
```

You can set the key in `.env`:

```env
OPENROUTER_API_KEY=sk-or-v1-...
```

Get a free key at <https://openrouter.ai/keys>. Or paste it into the sidebar — the app
writes it to `.env` so it is there next time.

Run it:

```powershell
streamlit run app.py
```

The app opens at <http://localhost:8501>. Press **Load demo plan** on the Generate tab to
try the interface without an API key.

---

## Sidebar

- **OpenRouter API key** — masked input. It is saved to `.env` on change and again right
  before generation. A caption confirms when a key is stored. Clear the field and click
  elsewhere to remove it.
- **Free model** — only free models are listed, with a `↻` button to refresh the catalog.
  The choice is saved as `OPENROUTER_MODEL`.
- **Custom model id** — collapsed by default; overrides the list when a model is not
  listed yet.
- **MCP endpoints** — collapsed by default; the label shows how many are configured.
- **Plan count** — shows how many plans are stored in `data/app.db`.

---

## Free models

The sidebar lists **only free models**, fetched live from OpenRouter. The list changes
often, so press **↻** next to the model selector if it looks stale. If the catalog cannot
be fetched, a small fallback list is shown and you can type any model id under
**Custom model id**.

Long plans (20-30 days) need a model with a large output limit. If a model truncates,
the app retries once with a request for a more compact answer. If it still comes back
short, the plan shows a warning instead of pretending it is complete.

---

## Optional MCP servers

Create a server at <https://mcp.pipedream.com/> and copy its streamable HTTP URL.

- **YouTube** — used after generation to search each topic. Only URLs returned by the
  search are marked "MCP verified".
- **Google Drive** — used when you press *Save to Google Drive*. The tool is chosen from
  the server's own schema; the app does not guess argument names.
- **Notion** — optional, reserved for page export.

Paste each URL in the sidebar and press **Test** in the *Connections* tab. A URL on its
own does nothing; the badge only turns green after a real health check.

---

## Tests

```powershell
pip install -r requirements-dev.txt
python -m pytest -q
```

The suite is offline: MCP and OpenRouter calls are mocked. It covers the models, storage,
exports, MCP parsing, YouTube link parsing, and `.env` settings writing.

---

## Privacy

- The API key is saved to `.env` on this machine when you enter it in the sidebar. `.env`
  is gitignored and never committed.
- Plans are stored in `data/app.db` on this machine. Delete that folder to wipe them.
- Only the text you type into the form is sent to OpenRouter.
- Video playback loads YouTube's embedded player; thumbnails come from `i.ytimg.com`.

---

## License

MIT. See [LICENSE](LICENSE).
