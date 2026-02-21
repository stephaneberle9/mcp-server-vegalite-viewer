import { useApp, useHostStyles } from "@modelcontextprotocol/ext-apps/react";
import { useEffect, useRef, useState } from "react";
import embed from "vega-embed";
import {
  THEMES,
  buildThemeConfig,
  getThemePrimaryColor,
  stripMarkColor,
} from "./themes";

// Fixed zoom levels: finer steps below 100%, coarser above.
const ZOOM_LEVELS = [0.75, 0.875, 1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5];
const ZOOM_DEFAULT_IDX = ZOOM_LEVELS.indexOf(1.0);

export default function App() {
  const [toolResult, setToolResult] = useState<any>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const embedResultRef = useRef<Awaited<ReturnType<typeof embed>> | null>(null);
  const [spec, setSpec] = useState<object | null>(null);
  const [theme, setTheme] = useState("default");
  const [zoomIdx, setZoomIdx] = useState(ZOOM_DEFAULT_IDX);
  const [error, setError] = useState<string | null>(null);

  // useApp creates the App instance and connects it. onAppCreated lets us
  // register handlers before connect() is called.
  const { app } = useApp({
    appInfo: { name: "Vega-Lite Viewer", version: "1.0.0" },
    capabilities: {},
    onAppCreated: (a) => {
      a.ontoolresult = (result: any) => setToolResult(result);
    },
  });

  // Apply the host's color-scheme and CSS variables so that CSS system colors
  // (ButtonFace, ButtonText, CanvasText, …) resolve correctly in dark mode.
  useHostStyles(app);

  // Parse the spec from the tool result.
  useEffect(() => {
    if (!toolResult) return;
    const text = toolResult.content?.find((c: any) => c.type === "text")?.text;
    if (!text) return;
    try {
      setSpec(JSON.parse(text));
      setError(null);
    } catch (e: any) {
      setError(String(e));
    }
  }, [toolResult]);

  // Re-embed whenever the spec or theme changes.
  useEffect(() => {
    if (!spec || !containerRef.current) return;

    embedResultRef.current?.finalize();

    // When a theme is active, strip explicit mark.color/fill from the spec so the
    // theme config can override AI-generated specs that hardcode mark colors.
    // Also pass buildThemeConfig via the `config` option (not the `theme` string
    // option) so bar.color gets baked into encodings, working around vega-lite's
    // rect→style.rect redirect that would otherwise leave bars unthemed.
    const specToEmbed =
      getThemePrimaryColor(theme) !== undefined ? stripMarkColor(spec) : spec;
    embed(containerRef.current, specToEmbed, {
      actions: false,
      ...(theme !== "default" && { config: buildThemeConfig(theme) }),
    }).then((r) => {
      embedResultRef.current = r;
    });

    return () => {
      embedResultRef.current?.finalize();
      embedResultRef.current = null;
    };
  }, [spec, theme]);

  if (error)
    return (
      <p style={{ color: "red", fontFamily: "sans-serif", padding: "8px" }}>
        Error: {error}
      </p>
    );

  if (!spec) return null;

  const themeEntry = THEMES.find((t) => t.value === theme);
  const themeBg = themeEntry?.bg;
  const themeTextColor = themeEntry?.textColor;
  const primaryColor = getThemePrimaryColor(theme);

  // When the theme defines an explicit background, use theme-specific toolbar
  // colors so the controls remain readable regardless of the host's dark/light
  // mode. Otherwise fall back to CSS system colors that adapt automatically.
  const hasBg = !!themeBg;
  const isDarkBg = themeBg === "#333";
  const toolbarDim = hasBg ? (isDarkBg ? "#888" : "#777") : "GrayText";
  const btnThemeStyle: React.CSSProperties = hasBg
    ? {
        ...btnBaseStyle,
        background: isDarkBg ? "#555" : "#f0f0f0",
        border: `1px solid ${isDarkBg ? "#666" : "#bbb"}`,
        color: themeTextColor ?? "#333",
      }
    : btnBaseStyle;
  const selectThemeStyle: React.CSSProperties = hasBg
    ? {
        ...selectDefaultStyle,
        background: isDarkBg ? "#555" : "#fff",
        border: `1px solid ${isDarkBg ? "#666" : "#bbb"}`,
        color: themeTextColor ?? "#333",
      }
    : selectDefaultStyle;

  return (
    <div
      style={{
        display: "inline-flex",
        flexDirection: "column",
        gap: 6,
        ...(themeBg ? { background: themeBg, padding: 8, borderRadius: 4 } : {}),
      }}
    >
      {/* Toolbar */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          fontFamily: "sans-serif",
          fontSize: 13,
          color: themeTextColor ?? "CanvasText",
        }}
      >
        {/* Zoom controls */}
        <button
          onClick={() => setZoomIdx((i) => i - 1)}
          disabled={zoomIdx === 0}
          title="Zoom out"
          style={btnThemeStyle}
        >
          −
        </button>
        <span style={{ minWidth: 42, textAlign: "center", userSelect: "none" }}>
          {ZOOM_LEVELS[zoomIdx] * 100 + "%"}
        </span>
        <button
          onClick={() => setZoomIdx((i) => i + 1)}
          disabled={zoomIdx === ZOOM_LEVELS.length - 1}
          title="Zoom in"
          style={btnThemeStyle}
        >
          +
        </button>

        <span style={{ color: toolbarDim }}>│</span>

        {/* Theme selector */}
        <label htmlFor="theme-select" style={{ color: toolbarDim }}>
          Theme:
        </label>
        <select
          id="theme-select"
          value={theme}
          onChange={(e) => setTheme(e.target.value)}
          style={selectThemeStyle}
        >
          {THEMES.map((t) => (
            <option key={t.value} value={t.value}>
              {t.label}
            </option>
          ))}
        </select>

        {/* Primary-color swatch: visual proof the theme is active */}
        {primaryColor && (
          <span
            title={primaryColor}
            style={{
              display: "inline-block",
              width: 12,
              height: 12,
              borderRadius: "50%",
              background: primaryColor,
              border: `1px solid ${isDarkBg ? "#666" : "#aaa"}`,
              flexShrink: 0,
            }}
          />
        )}
      </div>

      {/* Chart — zoom applied via CSS zoom property which adjusts layout */}
      <div style={{ zoom: ZOOM_LEVELS[zoomIdx] } as React.CSSProperties}>
        <div ref={containerRef} />
      </div>
    </div>
  );
}

const btnBaseStyle: React.CSSProperties = {
  width: 28,
  height: 28,
  fontSize: 16,
  lineHeight: 1,
  border: "1px solid ButtonBorder",
  borderRadius: 4,
  background: "ButtonFace",
  color: "ButtonText",
  cursor: "pointer",
  padding: 0,
};

const selectDefaultStyle: React.CSSProperties = {
  fontSize: 13,
  padding: "2px 4px",
  borderRadius: 4,
  border: "1px solid ButtonBorder",
  background: "ButtonFace",
  color: "ButtonText",
  cursor: "pointer",
};
