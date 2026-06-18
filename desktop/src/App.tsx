import { useState } from "react";
import { ThemeProvider } from "@/lib/theme-context";
import { ConfigScreen } from "@/screens/ConfigScreen";
import { RunningScreen } from "@/screens/RunningScreen";

type Screen = "config" | "running";

export default function App() {
  const [screen, setScreen] = useState<Screen>("config");

  return (
    <ThemeProvider>
      <div className="h-screen w-screen overflow-hidden bg-background text-foreground">
        {screen === "config" ? (
          <ConfigScreen onStart={() => setScreen("running")} />
        ) : (
          <RunningScreen onStop={() => setScreen("config")} />
        )}
      </div>
    </ThemeProvider>
  );
}
