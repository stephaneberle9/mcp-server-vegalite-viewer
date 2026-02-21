# Plan: Replace browser/WebSocket stack with MCP Apps

## Context
MCP Apps (extension `io.modelcontextprotocol/ui`) allow tool results to be rendered as
interactive UIs directly inside Claude Desktop / web, without a separate browser window.
This makes the entire FastAPI + uvicorn + WebSocket + web_browser infrastructure obsolete.
The new architecture has the `visualize_data` tool return the Vega-Lite spec as a text
result, and a `ui://` MCP resource serve a bundled React + Vega-Embed app that renders it
inline in the chat.

---

## Files to DELETE
- `src/mcp_server_vegalite_viewer/web_server.py`
- `src/mcp_server_vegalite_viewer/viewer_manager.py`
- `src/mcp_server_vegalite_viewer/web_browser.py`
- `src/mcp_server_vegalite_viewer/resources/viewer.html`
- `src/mcp_server_vegalite_viewer/resources/sample-visualization-spec.json`

---

## New directory: `app/`
React + Vite app. Its single-file build output is committed to
`src/mcp_server_vegalite_viewer/resources/viewer_app.html` so users need no Node.js to
run the server.

### `app/package.json`
```json
{
  "name": "vegalite-viewer-app",
  "private": true,
  "scripts": {
    "build": "vite build",
    "dev": "vite"
  },
  "dependencies": {
    "@modelcontextprotocol/ext-apps": "^0.4.0",
    "react": "^19",
    "react-dom": "^19",
    "vega-embed": "^6"
  },
  "devDependencies": {
    "@types/react": "^19",
    "@types/react-dom": "^19",
    "vite": "^6",
    "vite-plugin-singlefile": "^2"
  }
}
```

### `app/vite.config.ts`
```ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { viteSingleFile } from "vite-plugin-singlefile";

export default defineConfig({
  plugins: [react(), viteSingleFile()],
  build: {
    outDir: "../src/mcp_server_vegalite_viewer/resources",
    emptyOutDir: false,
    rollupOptions: { input: "index.html" },
  },
});
```
Output: `src/mcp_server_vegalite_viewer/resources/index.html`
→ rename/configure output filename to `viewer_app.html`
(use `rollupOptions.output.entryFileNames` or rename in build script)

### `app/index.html`
```html
<!DOCTYPE html>
<html>
  <head><meta charset="UTF-8" /><meta name="color-scheme" content="light dark" /></head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

### `app/src/main.tsx`
```tsx
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
createRoot(document.getElementById("root")!).render(<StrictMode><App /></StrictMode>);
```

### `app/src/App.tsx`
```tsx
import { useApp } from "@modelcontextprotocol/ext-apps/react";
import { useEffect, useRef, useState } from "react";
import embed from "vega-embed";

export default function App() {
  const { toolResult } = useApp();
  const containerRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!toolResult || !containerRef.current) return;
    const text = toolResult.content?.find((c: any) => c.type === "text")?.text;
    if (!text) return;
    try {
      const spec = JSON.parse(text);
      setError(null);
      embed(containerRef.current, spec, { actions: true });
    } catch (e: any) {
      setError(e.message);
    }
  }, [toolResult]);

  if (!toolResult) return <p style={{ color: "gray" }}>Waiting for visualization…</p>;
  if (error) return <p style={{ color: "red" }}>Error: {error}</p>;
  return <div ref={containerRef} />;
}
```

### Build command
```bash
cd app && npm install && npm run build
```
Output file: `src/mcp_server_vegalite_viewer/resources/viewer_app.html`
This file is **committed to the repo**.

---

## Modified: `pyproject.toml`
Remove dependencies: `fastapi`, `uvicorn[standard]`, `httpx`, `psutil`
(nothing new to add — Vega-Lite and ext-apps are bundled into the HTML)

---

## Modified: `src/mcp_server_vegalite_viewer/mcp_server.py`

### Remove
- `mcp_lifespan` context manager and `lifespan=` from `FastMCP(...)`
- `_web_server_controller` instance
- Imports: `fastmcp` (module-level import; keep `from fastmcp import ...`), `httpx`,
  `asynccontextmanager`, `AsyncIterator`
- Imports from `.web_server` and `.web_browser`
- `VegaLiteViewerError` exception class
- The HTTP POST to `/live-data` and web browser open call in `visualize_data`

### Add
```python
import importlib.resources as pkg_resources
from fastmcp.server.apps import AppConfig, ResourceCSP

APP_RESOURCE_URI = "ui://vegalite-viewer/view.html"

@mcp.resource(
    APP_RESOURCE_URI,
    app=AppConfig(
        csp=ResourceCSP(resource_domains=["https://cdn.jsdelivr.net"])
    ),
)
def vegalite_viewer_app() -> str:
    return pkg_resources.read_text(
        "mcp_server_vegalite_viewer.resources", "viewer_app.html"
    )
```

Note: CSP `resource_domains` is needed only if the bundled HTML still loads anything from
CDN (vite-plugin-singlefile inlines everything, so CSP may be empty — verify after build).

### Modify `visualize_data`
- Add `app=AppConfig(resource_uri=APP_RESOURCE_URI)` to `@mcp.tool(...)`
- Replace the entire HTTP POST block at the end with:
  ```python
  return json.dumps(vegalite_specification)
  ```
- Remove the `web_browser.open(...)` call
- Return type stays `str`

### Update tool description
Remove the sentence about the web browser opening automatically.

### FastMCP constructor
```python
mcp = FastMCP("Vega-Lite")   # no lifespan=
```

---

## Modified: `src/mcp_server_vegalite_viewer/__main__.py`

### Remove
- `--port` / `-p` CLI argument
- `--lazy-view` CLI argument
- `web_browser.open(args.port)` call
- `fastmcp.settings.port = args.port` hack
- Import of `web_browser` and `LOCALHOST`
- `VegaLiteViewerError` import and its `BaseExceptionGroup` handler
  (no lifespan errors possible anymore)

### Keep
- `--silent` / `--debug` logging flags
- Log file setup
- `mcp.run(transport="stdio", log_level=...)` call

---

## Modified: `CLAUDE.md`
- Remove `--port` from run examples
- Add note about the `app/` build step:
  ```
  cd app && npm install && npm run build
  ```

---

## Verification
1. Build the React app: `cd app && npm install && npm run build`
   → `src/mcp_server_vegalite_viewer/resources/viewer_app.html` is created
2. Run the server: `uv run mcp-server-vegalite-viewer`
3. Connect via MCP Inspector and call `upload_data` then `visualize_data`
4. In Claude Desktop (or a client that supports MCP Apps), the chart should render
   inline in the chat instead of opening a browser window
5. Run type checks: `uv run pre-commit run --all-files`
