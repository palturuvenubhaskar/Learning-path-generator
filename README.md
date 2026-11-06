# Learning Path Generator

Describe what you want to learn, how much time you have per day, and for how long.
The app asks a free model on [OpenRouter](https://openrouter.ai) for a day-by-day
study plan, validates it, and shows it as an interactive checklist.

Plans and progress are saved locally in SQLite, so a refresh does not lose your work.

---

## What it actually does

| Step | Detail |
| :--- | :--- |
| Input | A Pydantic model validates level, format, duration (max 30 days) and daily time per unit. |
| Generation | One OpenRouter chat request returns a JSON object. Malformed or truncated output is repaired once. |
| Validation | `LearningRoadmap` validates the JSON and renumbers days so keys can never collide. |
| MCP (optional) | A YouTube MCP server is used to search real links. Only returned URLs get a "verified" label. |
| Storage | Plans and checkboxes live in `data/app.db`. |
| Export | Markdown, JSON, or an upload through a Google Drive MCP server. |

**Honest limits:** free models are rate-limited and sometimes return broken JSON.
Links without a "verified" label are model suggestions, not checked facts.
Plans are capped at 30 days; longer requests are shortened and flagged on screen.

---

## Project structure

```
app.py                  # entry point
dashboard.py            # page setup, sidebar, navigation, routing
config.py               # environment and paths
models.py               # Pydantic schemas and validation
ai_generator.py         # OpenRouter request, JSON repair, validation
openrouter_models.py    # live catalog of free models
mcp_client.py           # MCP health checks, YouTube search, Drive upload
exporter.py             # Markdown / JSON / Drive export
storage.py              # SQLite persistence
ui/
  theme.py              # CSS and small render helpers
  state.py              # session state and navigation
  demo_data.py          # loads assets/demo_roadmap.json
  views/
    generate.py         # the request form
    roadmap.py          # the active plan
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
copy .env.example .env
```

Open `.env` and set:

```env
OPENROUTER_API_KEY=sk-or-v1-...
```

Get a free key at <https://openrouter.ai/keys>. You can also paste it into the app
sidebar; it is kept in memory only and never written to disk.

Run it:

```powershell
streamlit run app.py
```

The app opens at <http://localhost:8501>.

---

## Free models

The sidebar lists **only free models**, fetched live from OpenRouter. The list changes
often, so press **Refresh model list** if it looks stale. If the catalog cannot be
fetched, a small fallback list is shown and you can type any model id under
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

The suite is offline: MCP and OpenRouter calls are mocked.

---

## Privacy

- The API key stays in the Streamlit session.
- Plans are stored in `data/app.db` on this machine. Delete that folder to wipe them.
- Only the text you type into the form is sent to OpenRouter.

---

## License

MIT. See [LICENSE](LICENSE).
