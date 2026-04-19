import { invoke } from "@tauri-apps/api/core";
import { defaultConfig, type Config } from "$lib/types";

export const config = $state<Config>(defaultConfig());

let loaded = false;

export async function loadConfig() {
  const remote = await invoke<Config>("load_config");
  Object.assign(config, remote);
  loaded = true;
}

export function isLoaded() {
  return loaded;
}

export async function saveConfig() {
  await invoke("save_config", { config: $state.snapshot(config) });
}
