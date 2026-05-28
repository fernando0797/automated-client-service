import { Link } from "@tanstack/react-router";

export function Header() {
  return (
    <header className="sticky top-0 z-20 border-b border-border bg-card/90 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center gap-4 px-6 py-3">
        <Link to="/" className="text-xl font-bold tracking-tight text-primary">
          Fer&amp;Vic
        </Link>
        <div className="mx-4 flex-1">
          <input
            type="search"
            placeholder="Search products, orders or help..."
            className="w-full rounded-full border border-border bg-background px-4 py-2 text-sm outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/20"
          />
        </div>
        <div className="flex items-center gap-2">
          <button className="rounded-full border border-border bg-background px-4 py-2 text-sm font-medium text-foreground transition hover:bg-secondary">
            My account
          </button>
          <button className="rounded-full bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition hover:bg-primary/90">
            Cart
          </button>
        </div>
      </div>
    </header>
  );
}
