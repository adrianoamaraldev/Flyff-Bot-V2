const BASE = "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export const api = {
  health: () => request<{ status: string }>("/health"),

  bot: {
    start:  () => request<{ status: string }>("/bot/start",  { method: "POST" }),
    ready:  () => request<{ status: string }>("/bot/ready",  { method: "POST" }),
    stop:   () => request<{ status: string }>("/bot/stop",   { method: "POST" }),
    pause:  () => request<{ status: string }>("/bot/pause",  { method: "POST" }),
    resume: () => request<{ status: string }>("/bot/resume", { method: "POST" }),
    status: () => request<BotStatus>("/bot/status"),
  },

  config: {
    get:    ()           => request<BotConfig>("/config"),
    update: (data: BotConfig) => request<{ status: string }>("/config", {
      method: "PUT",
      body: JSON.stringify(data),
    }),
  },

  monsters: {
    list: () => request<{ monsters: string[] }>("/monsters"),
  },
};

export type BotStatus = {
  state: string;
  running: boolean;
  paused: boolean;
  hp: number;
  mp: number;
  fp: number;
  stats: {
    kills: number;
  };
};

export type SkillConfig = {
  key: string;
  cooldown: number;
};

export type BotConfig = {
  browser:   { headless: boolean; width: number; height: number; game_url: string };
  farm:      { attack_timeout: number; action_delay: number };
  character: { hp_threshold: number; hp_potion_key: string; mp_threshold: number; mp_potion_key: string; fp_threshold: number; fp_potion_key: string; potion_cooldown: number };
  skills:    { rotation: SkillConfig[]; skill_delay: number };
  loot: { loot_key: string; auto_loot: boolean; loot_delay: number; loot_duration: number };
  vision:    { detection_confidence: number; name_click_offset_y: number; selected_monster: string };
  logging:   { level: string; save_to_file: boolean; visual_overlay: boolean };
};


export type LogEntry = {
  time: string;
  level: "DEBUG" | "INFO" | "SUCCESS" | "WARNING" | "ERROR" | "CRITICAL";
  message: string;
};
