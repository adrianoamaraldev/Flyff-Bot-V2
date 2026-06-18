import { useEffect, useState } from "react";
import { Plus, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Section } from "@/components/ui/section";
import type { SkillConfig } from "@/lib/api";

function Root({ children }: { children: React.ReactNode }) {
  return <Section title="Rotação de Skills"><div className="space-y-3">{children}</div></Section>;
}

function Item({
  skill,
  index,
  onChange,
  onRemove,
  canRemove,
}: {
  skill: SkillConfig;
  index: number;
  onChange: (index: number, field: keyof SkillConfig, value: string | number) => void;
  onRemove: (index: number) => void;
  canRemove: boolean;
}) {
  const [cooldownStr, setCooldownStr] = useState(String(skill.cooldown));

  useEffect(() => {
    setCooldownStr(String(skill.cooldown));
  }, [skill.cooldown]);

  function commitCooldown(raw: string) {
    const val = parseFloat(raw);
    const parsed = isNaN(val) || val < 0 ? 0 : val;
    setCooldownStr(String(parsed));
    onChange(index, "cooldown", parsed);
  }

  return (
    <div className="flex items-end gap-2">
      <div className="flex flex-col gap-1">
        <Label className="text-xs text-muted-foreground">Tecla</Label>
        <Input
          value={skill.key}
          maxLength={4}
          className="h-7 w-12 text-center font-mono uppercase text-xs"
          onChange={(e) => onChange(index, "key", e.target.value.toUpperCase())}
        />
      </div>
      <div className="flex flex-col gap-1">
        <Label className="text-xs text-muted-foreground">Cooldown (s)</Label>
        <Input
          type="number"
          min={0}
          step={0.5}
          value={cooldownStr}
          className="h-7 w-20 text-center text-xs"
          onChange={(e) => setCooldownStr(e.target.value)}
          onBlur={(e) => commitCooldown(e.target.value)}
        />
      </div>
      <Button
        variant="ghost"
        size="icon"
        className="h-7 w-7 text-destructive hover:text-destructive shrink-0"
        disabled={!canRemove}
        onClick={() => onRemove(index)}
      >
        <Trash2 className="h-3.5 w-3.5" />
      </Button>
    </div>
  );
}

function AddButton({ onClick }: { onClick: () => void }) {
  return (
    <Button variant="outline" size="sm" className="w-full gap-1" onClick={onClick}>
      <Plus className="h-3.5 w-3.5" />
      Adicionar Skill
    </Button>
  );
}

export const SkillsConfig = { Root, Item, AddButton };
