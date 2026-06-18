import { useEffect, useRef } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { LogEntry } from "@/lib/api";

const LEVEL_COLORS: Record<LogEntry["level"], string> = {
  DEBUG:    "text-muted-foreground",
  INFO:     "text-foreground",
  SUCCESS:  "text-green-500",
  WARNING:  "text-yellow-500",
  ERROR:    "text-red-500",
  CRITICAL: "text-red-600 font-bold",
};

function Root({ children }: { children: React.ReactNode }) {
  return (
    <Card className="flex flex-col flex-1 min-h-0">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">Log ao Vivo</CardTitle>
      </CardHeader>
      <CardContent className="flex-1 min-h-0 p-0 px-4 pb-4">
        {children}
      </CardContent>
    </Card>
  );
}

function Entries({ entries }: { entries: LogEntry[] }) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [entries]);

  return (
    <ScrollArea className="h-full rounded border bg-muted/30 p-2">
      <div className="space-y-0.5 font-mono text-xs">
        {entries.map((entry, i) => (
          <div key={i} className="flex gap-2">
            <span className="text-muted-foreground shrink-0">{entry.time}</span>
            <span className={`shrink-0 w-16 ${LEVEL_COLORS[entry.level]}`}>
              {entry.level}
            </span>
            <span className="break-all">{entry.message}</span>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </ScrollArea>
  );
}

export const LogPanel = { Root, Entries };
