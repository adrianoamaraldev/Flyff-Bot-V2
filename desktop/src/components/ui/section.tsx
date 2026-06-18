function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-md border p-3 flex flex-col gap-4">
      <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">{title}</p>
      <div className="space-y-2.5">{children}</div>
    </div>
  );
}

export { Section };
