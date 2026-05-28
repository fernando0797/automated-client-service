import { Link } from "@tanstack/react-router";

export function Sidebar() {
  const baseBtn =
    "w-full rounded-xl px-4 py-3 text-left text-sm font-medium transition";
  return (
    <aside className="w-56 shrink-0">
      <nav className="sticky top-20 flex flex-col gap-2 rounded-2xl border border-border bg-card p-3 shadow-sm">
        <button className={`${baseBtn} text-foreground hover:bg-secondary`}>
          Catalog
        </button>
        <button className={`${baseBtn} text-foreground hover:bg-secondary`}>
          About us
        </button>
        <Link
          to="/support"
          className={`${baseBtn} bg-primary/10 text-primary hover:bg-primary/15`}
        >
          Support
        </Link>
      </nav>
    </aside>
  );
}
