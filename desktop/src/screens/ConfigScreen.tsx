import { useEffect, useState } from "react";
import { Play, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Slider } from "@/components/ui/slider";
import { Select, SelectContent, SelectItem, SelectTrigger } from "@/components/ui/select";
import { Section } from "@/components/ui/section";
import { SkillsConfig } from "@/components/config/SkillsConfig";
import { ThemeToggle } from "@/components/ThemeToggle";
import { api, type BotConfig, type SkillConfig } from "@/lib/api";

type Props = { onStart: () => void };

export function ConfigScreen({ onStart }: Props) {
  const [config, setConfig] = useState<BotConfig | null>(null);
  const [monsters, setMonsters] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.config.get().then(setConfig).catch(console.error);
    api.monsters.list().then(r => setMonsters(r.monsters)).catch(console.error);
  }, []);

  async function handleStart() {
    if (!config) return;
    setLoading(true);
    try {
      await api.config.update(config);
      await api.bot.start();
      onStart();
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  function updateSkill(index: number, field: keyof SkillConfig, value: string | number) {
    if (!config) return;
    const rotation = [...config.skills.rotation];
    rotation[index] = { ...rotation[index], [field]: value };
    setConfig({ ...config, skills: { ...config.skills, rotation } });
  }

  function addSkill() {
    if (!config) return;
    setConfig({ ...config, skills: { ...config.skills, rotation: [...config.skills.rotation, { key: "", cooldown: 0 }] } });
  }

  function removeSkill(index: number) {
    if (!config) return;
    setConfig({ ...config, skills: { ...config.skills, rotation: config.skills.rotation.filter((_, i) => i !== index) } });
  }

  if (!config) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <header className="grid grid-cols-3 items-center px-4 py-2.5 border-b shrink-0">
        <span className="text-xs text-muted-foreground font-medium">Flyff Bot</span>
        <h1 className="font-semibold text-sm text-center">Configuração</h1>
        <div className="flex justify-end"><ThemeToggle /></div>
      </header>

      {/* Scroll */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3">

        {/* Monstro */}
        <Section title="Monstro">
          <Select
            value={config.vision.selected_monster}
            onValueChange={(v) =>
              setConfig({ ...config, vision: { ...config.vision, selected_monster: v ?? "" } })
            }
          >
            <SelectTrigger className="h-8 w-full">
              <span className="flex flex-1 text-left text-sm text-foreground">
                {config.vision.selected_monster === "" ? "Todos" : config.vision.selected_monster}
              </span>
            </SelectTrigger>
            <SelectContent alignItemWithTrigger={false}>
              <SelectItem value="">Todos</SelectItem>
              {monsters.map((m) => <SelectItem key={m} value={m}>{m}</SelectItem>)}
            </SelectContent>
          </Select>
        </Section>

        {/* Skills */}
        <SkillsConfig.Root>
          {config.skills.rotation.map((skill, i) => (
            <SkillsConfig.Item
              key={i} skill={skill} index={i}
              onChange={updateSkill} onRemove={removeSkill}
              canRemove={config.skills.rotation.length > 1}
            />
          ))}
          <SkillsConfig.AddButton onClick={addSkill} />
        </SkillsConfig.Root>

        {/* Coleta */}
        <Section title="Coleta">
          <div className="flex items-center gap-4">
            <div className="flex flex-col gap-1">
              <Label className="text-xs text-muted-foreground">Tecla</Label>
              <Input
                value={config.loot.loot_key}
                maxLength={4}
                className="h-7 w-12 text-center font-mono uppercase text-xs"
                onChange={(e) => setConfig({ ...config, loot: { ...config.loot, loot_key: e.target.value } })}
              />
            </div>
            <div className="flex items-center gap-2 mt-4">
              <Label className="text-xs text-muted-foreground">Auto loot</Label>
              <Switch
                checked={config.loot.auto_loot}
                onCheckedChange={(v) => setConfig({ ...config, loot: { ...config.loot, auto_loot: v } })}
              />
            </div>
          </div>
        </Section>

        {/* Cura */}
        <Section title="Cura">
          {/* Teclas */}
          <div className="flex gap-3">
            {(["hp", "mp", "fp"] as const).map((bar) => (
              <div key={bar} className="flex flex-col gap-1">
                <Label className="text-xs text-muted-foreground">Tecla {bar.toUpperCase()}</Label>
                <Input
                  value={config.character[`${bar}_potion_key` as keyof typeof config.character] as string}
                  maxLength={4}
                  className="h-7 w-12 text-center font-mono uppercase text-xs"
                  onChange={(e) => setConfig({ ...config, character: { ...config.character, [`${bar}_potion_key`]: e.target.value } })}
                />
              </div>
            ))}
          </div>

          {/* Thresholds */}
          {(["hp", "mp", "fp"] as const).map((bar) => {
            const thresholdKey = `${bar}_threshold` as keyof typeof config.character;
            const pct = Math.round((config.character[thresholdKey] as number) * 100);
            return (
              <div key={bar} className="space-y-1">
                <div className="flex items-center justify-between">
                  <Label className="text-xs text-muted-foreground">{bar.toUpperCase()} abaixo de</Label>
                  <span className="text-xs font-medium">{pct}%</span>
                </div>
                <Slider
                  min={10} max={90} step={5}
                  value={[pct]}
                  onValueChange={(val) => {
                    const v = Array.isArray(val) ? val[0] : (val as number);
                    setConfig({ ...config, character: { ...config.character, [thresholdKey]: v / 100 } });
                  }}
                />
              </div>
            );
          })}
        </Section>

        {/* Detecção */}
        <Section title="Detecção">
          <div className="flex items-center justify-between">
            <Label className="text-xs text-muted-foreground">Confiança mínima</Label>
            <span className="text-xs font-medium">{Math.round(config.vision.detection_confidence * 100)}%</span>
          </div>
          <Slider
            min={30} max={95} step={5}
            value={[Math.round(config.vision.detection_confidence * 100)]}
            onValueChange={(val) => {
              const v = Array.isArray(val) ? val[0] : (val as number);
              setConfig({ ...config, vision: { ...config.vision, detection_confidence: v / 100 } });
            }}
          />
        </Section>

      </div>

      {/* Footer */}
      <div className="px-3 pb-3 pt-2 shrink-0">
        <Button className="w-full gap-2" onClick={handleStart} disabled={loading}>
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
          Iniciar Bot
        </Button>
      </div>
    </div>
  );
}
