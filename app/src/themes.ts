import * as vegaThemes from "vega-themes";

// Themes available in the dropdown — backgrounds match each theme's chart background
// so the toolbar visually integrates with the rendered chart.
export type Theme = {
  value: string;
  label: string;
  bg?: string;
  textColor?: string;
};

export const THEMES: Theme[] = [
  { value: "default",         label: "Default" },
  { value: "dark",            label: "Dark",            bg: "#333",    textColor: "#fff" },
  { value: "excel",           label: "Excel",           bg: "#fff",    textColor: "#333" },
  { value: "ggplot2",         label: "ggplot2",         bg: "#e5e5e5", textColor: "#333" },
  { value: "quartz",          label: "Quartz",          bg: "#f9f9f9", textColor: "#333" },
  { value: "vox",             label: "Vox",             bg: "#fff",    textColor: "#333" },
  { value: "fivethirtyeight", label: "FiveThirtyEight", bg: "#f0f0f0", textColor: "#333" },
  { value: "latimes",         label: "LA Times",        bg: "#ffffff", textColor: "#333" },
  { value: "googlecharts",    label: "Google Charts",   bg: "#fff",    textColor: "#333" },
  { value: "powerbi",         label: "Power BI",        bg: "#fff",    textColor: "#333" },
];

// When a non-default theme is active, strip explicit `color`/`fill` from the top-level
// mark definition so the theme config can control bar (and other mark) colors.
// Without this, AI-generated specs with e.g. `"mark":{"type":"bar","color":"#4f46e5"}`
// always override theme config regardless of the config option passed to embed.
export function stripMarkColor(spec: object): object {
  const s = spec as any;
  if (!s.mark || typeof s.mark !== "object") return spec;
  const { color, fill, ...rest } = s.mark;
  if (color === undefined && fill === undefined) return spec;
  return { ...s, mark: rest };
}

// Returns the primary mark color for a theme (used in the toolbar color swatch).
// rect.fill is Vega's fill for rectangle primitives; if not set (e.g. dark theme),
// fall back to the first category palette color.
export function getThemePrimaryColor(themeName: string): string | undefined {
  if (themeName === "default") return undefined;
  const allThemes = vegaThemes as Record<string, any>;
  const tc = allThemes[themeName];
  if (!tc || typeof tc !== "object" || Array.isArray(tc)) return undefined;
  return tc.rect?.fill ?? tc.range?.category?.[0];
}

// vega-themes defines mark colors using Vega mark type names (rect, arc, symbol, …).
// vega-lite's stripAndRedirectConfig redirects config.rect → config.style.rect, which
// only applies to `rect` marks — NOT to `bar` marks. We fix this by also setting
// config.bar.color from the theme's primary mark color, so bar charts get themed too.
export function buildThemeConfig(
  themeName: string
): Record<string, unknown> | undefined {
  if (themeName === "default") return undefined;
  const allThemes = vegaThemes as Record<string, unknown>;
  const themeConfig = allThemes[themeName];
  if (
    !themeConfig ||
    typeof themeConfig !== "object" ||
    Array.isArray(themeConfig)
  )
    return undefined;
  const tc = themeConfig as Record<string, any>;
  // bar.color is Vega-Lite's mark config for bar marks; it gets redirected to
  // config.style.bar by stripAndRedirectConfig, which DOES apply to bar marks.
  const primary = getThemePrimaryColor(themeName);
  if (!primary) return tc as Record<string, unknown>;
  return { ...tc, bar: { color: primary, ...(tc.bar ?? {}) } };
}
