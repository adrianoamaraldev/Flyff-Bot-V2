import { Play, Pause, Square, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";

function Root({ children }: { children: React.ReactNode }) {
  return <div className="flex items-center gap-2">{children}</div>;
}

function LoginBanner({ onReady }: { onReady: () => void }) {
  return (
    <div className="flex items-center gap-3 rounded-lg border border-yellow-500/40 bg-yellow-500/10 px-4 py-3 w-full">
      <CheckCircle2 className="h-4 w-4 text-yellow-500 shrink-0" />
      <p className="text-sm text-yellow-600 dark:text-yellow-400 flex-1">
        Faça login no jogo e vá até a área de farm.
      </p>
      <Button size="sm" onClick={onReady}>
        Pronto
      </Button>
    </div>
  );
}

function Actions({
  state,
  onPause,
  onResume,
  onStop,
}: {
  state: string;
  onPause: () => void;
  onResume: () => void;
  onStop: () => void;
}) {
  const isPaused = state === "PAUSED";
  return (
    <>
      {isPaused ? (
        <Button variant="outline" size="sm" className="gap-1.5" onClick={onResume}>
          <Play className="h-3.5 w-3.5" /> Retomar
        </Button>
      ) : (
        <Button variant="outline" size="sm" className="gap-1.5" onClick={onPause}>
          <Pause className="h-3.5 w-3.5" /> Pausar
        </Button>
      )}
      <Button variant="destructive" size="sm" className="gap-1.5" onClick={onStop}>
        <Square className="h-3.5 w-3.5" /> Parar
      </Button>
    </>
  );
}

export const BotControls = { Root, LoginBanner, Actions };
