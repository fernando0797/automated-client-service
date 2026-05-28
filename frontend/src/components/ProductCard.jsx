export function ProductCard({ name, category, description, emoji }) {
  return (
    <div className="group flex flex-col overflow-hidden rounded-2xl border border-border bg-card shadow-sm transition hover:-translate-y-0.5 hover:shadow-md">
      <div className="flex h-40 items-center justify-center bg-gradient-to-br from-primary/10 to-secondary text-6xl">
        <span aria-hidden>{emoji}</span>
      </div>
      <div className="flex flex-1 flex-col gap-2 p-5">
        <span className="text-xs font-medium uppercase tracking-wide text-primary">
          {category}
        </span>
        <h3 className="text-lg font-semibold text-foreground">{name}</h3>
        <p className="flex-1 text-sm text-muted-foreground">{description}</p>
        <button className="mt-3 w-full rounded-full bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition hover:bg-primary/90">
          View product
        </button>
      </div>
    </div>
  );
}
