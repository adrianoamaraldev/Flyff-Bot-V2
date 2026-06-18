import { useEffect, useRef, useState } from "react";
import { BotControls } from "@/components/dashboard/BotControls";
import { BotStats } from "@/components/dashboard/BotStats";
import { LogPanel } from "@/components/dashboard/LogPanel";
import { ThemeToggle } from "@/components/ThemeToggle";
import { api, type BotStatus, type LogEntry } from "@/lib/api";

type Props = {
  onStop: () => void;
};

export function RunningScreen({ onStop }: Props) {
  const [status, setStatus] = useState<BotStatus>({
    state: "IDLE",
    running: false,
    paused: false,
    hp: 1, mp: 0, fp: 0,
    stats: { kills: 0 },
  });
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [waitingLogin, setWaitingLogin] = useState(true);
  const wsRef = useRef<WebSocket | null>(null);
  // Só redireciona para config depois que o bot realmente rodou ao menos uma vez
  const wasRunning = useRef(false);

  // Polling de status a cada 1.5s
  useEffect(() => {
    const id = setInterval(async () => {
      try {
        const s = await api.bot.status();
        setStatus(s);
        if (s.running) wasRunning.current = true;
        if (wasRunning.current && !s.running) {
          onStop();
        }
      } catch {}
    }, 1000);
    return () => clearInterval(id);
  }, [onStop]);

  // WebSocket de logs com delay (evita ruído do StrictMode) e auto-reconexão
  useEffect(() => {
    let alive = true;

    function connect() {
      if (!alive) return;
      const ws = new WebSocket("ws://localhost:8000/ws/logs");
      wsRef.current = ws;
      ws.onmessage = (e) => {
        try { setLogs((prev) => [...prev.slice(-300), JSON.parse(e.data)]); } catch {}
      };
      ws.onclose = () => {
        if (alive) setTimeout(connect, 2000);
      };
    }

    const timer = setTimeout(connect, 200);
    return () => {
      alive = false;
      clearTimeout(timer);
      wsRef.current?.close();
    };
  }, []);

  async function handleReady() {
    try {
      await api.bot.ready();
      setWaitingLogin(false);
    } catch (e) {
      console.error(e);
    }
  }

  async function handlePause() {
    try { await api.bot.pause(); } catch {}
  }

  async function handleResume() {
    try { await api.bot.resume(); } catch {}
  }

  async function handleStop() {
    try {
      await api.bot.stop();
      onStop();
    } catch {}
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <header className="flex items-center justify-between px-4 py-3 border-b shrink-0">
        <div className="flex items-center gap-2">
          <h1 className="font-semibold text-sm">Flyff Bot</h1>
          <BotStats.StateBadge state={status.state} />
        </div>
        <ThemeToggle />
      </header>

      {/* Body */}
      <div className="flex-1 flex flex-col gap-4 p-4 min-h-0">

        {/* Banner de login */}
        {waitingLogin && (
          <BotControls.Root>
            <BotControls.LoginBanner onReady={handleReady} />
          </BotControls.Root>
        )}

        {/* Stats */}
        {!waitingLogin && (
          <BotStats.Root>
            <BotStats.StatsGrid stats={status.stats} />
            <BotStats.Bars
              hp={status.hp ?? 1}
              mp={status.mp ?? 0}
              fp={status.fp ?? 0}
            />
          </BotStats.Root>
        )}

        {/* Log */}
        <LogPanel.Root>
          <LogPanel.Entries entries={logs} />
        </LogPanel.Root>
      </div>

      {/* Footer — controles */}
      {!waitingLogin && (
        <div className="px-4 pb-4 shrink-0">
          <BotControls.Root>
            <BotControls.Actions
              state={status.state}
              onPause={handlePause}
              onResume={handleResume}
              onStop={handleStop}
            />
          </BotControls.Root>
        </div>
      )}
    </div>
  );
}
