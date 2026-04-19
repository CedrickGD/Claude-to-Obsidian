import type { Theme } from "$lib/types";

const STORAGE_KEY = "c2o_theme";

function systemPrefersDark(): boolean {
  if (typeof window === "undefined") return false;
  return window.matchMedia("(prefers-color-scheme: dark)").matches;
}

function applyDarkClass(isDark: boolean) {
  if (typeof document === "undefined") return;
  document.documentElement.classList.toggle("dark", isDark);
}

export function isResolvedDark(theme: Theme): boolean {
  if (theme === "dark") return true;
  if (theme === "light") return false;
  return systemPrefersDark();
}

export function applyTheme(theme: Theme) {
  applyDarkClass(isResolvedDark(theme));
  try {
    if (theme === "auto") localStorage.removeItem(STORAGE_KEY);
    else localStorage.setItem(STORAGE_KEY, theme);
  } catch {
    // ignore storage errors
  }
}

export function watchSystemTheme(getTheme: () => Theme): () => void {
  if (typeof window === "undefined") return () => {};
  const mql = window.matchMedia("(prefers-color-scheme: dark)");
  const handler = () => {
    if (getTheme() === "auto") applyDarkClass(systemPrefersDark());
  };
  mql.addEventListener("change", handler);
  return () => mql.removeEventListener("change", handler);
}
