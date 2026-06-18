import { Swords } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { BotStatus } from "@/lib/api";

const STATE_COLORS: Record<string, string> = {
  IDLE:      "secondary",
  SCANNING:  "outline",
  ATTACKING: "destructive",
  LOOTING:   "default",
  PAUSED:    "secondary",
  STOPPED:   "secondary",
} as const;

function StateBadge({ state }: { state: string }) {
  const variant = (STATE_COLORS[state] ?? "outline") as "default" | "secondary" | "destructive" | "outline";
  return <Badge variant={variant}>{state}</Badge>;
}

function StatsGrid({ stats }: { stats: BotStatus["stats"] }) {
  return (
    <div className="flex items-center gap-2 rounded-md border px-3 py-2">
      <Swords className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
      <span className="text-xs text-muted-foreground">Kills</span>
      <span className="ml-auto text-sm font-bold tabular-nums">{stats.kills ?? 0}</span>
    </div>
  );
}

type BarColor = "red" | "blue" | "green";

const BAR_COLORS: Record<BarColor, { fill: string; label: string }> = {
  red:   { fill: "bg-red-500",   label: "HP" },
  blue:  { fill: "bg-blue-500",  label: "MP" },
  green: { fill: "bg-green-500", label: "FP" },
};

function StatBar({ value, color }: { value: number; color: BarColor }) {
  const pct = Math.round(value * 100);
  const { fill, label } = BAR_COLORS[color];
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between">
        <span className="text-xs text-muted-foreground">{label}</span>
        <span className="text-xs font-medium tabular-nums">{pct}%</span>
      </div>
      <div className="relative h-2 w-full overflow-hidden rounded-full bg-muted">
        <div className={cn("h-full transition-all duration-500", fill)} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

function Bars({ hp, mp, fp }: { hp: number; mp: number; fp: number }) {
  return (
    <div className="space-y-2">
      <StatBar value={hp} color="red" />
      <StatBar value={mp} color="blue" />
      <StatBar value={fp} color="green" />
    </div>
  );
}

function Root({ children }: { children: React.ReactNode }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">Status</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">{children}</CardContent>
    </Card>
  );
}

export const BotStats = { Root, StateBadge, StatsGrid, Bars };
