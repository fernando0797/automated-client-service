import { createFileRoute, Link } from "@tanstack/react-router";
import { Header } from "@/components/Header";
import { Sidebar } from "@/components/Sidebar";
import { ProductCard } from "@/components/ProductCard";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Fer&Vic — Simple technology, intelligent support" },
      {
        name: "description",
        content:
          "Fer&Vic selects everyday tech products and provides intelligent support whenever you need help.",
      },
      { property: "og:title", content: "Fer&Vic — Simple technology, intelligent support" },
      {
        property: "og:description",
        content: "Everyday tech with intelligent customer support.",
      },
    ],
  }),
  component: HomePage,
});

const products = [
  {
    name: "Amazon Kindle",
    category: "Digital reading",
    description: "A lightweight e-reader for reading anywhere.",
    emoji: "📖",
  },
  {
    name: "Bose SoundLink Speaker",
    category: "Audio",
    description: "A portable Bluetooth speaker with powerful sound.",
    emoji: "🔊",
  },
  {
    name: "Canon EOS",
    category: "Photography",
    description: "A digital camera for high-quality photography.",
    emoji: "📷",
  },
  {
    name: "Fitbit Charge",
    category: "Wearables",
    description: "An activity tracker for health, fitness and daily monitoring.",
    emoji: "⌚",
  },
];

const trustPoints = [
  "Intelligent support by product",
  "Issue tracking by ticket",
  "Responses adapted to the type of request",
  "Escalation to a human agent when needed",
];

function HomePage() {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <div className="mx-auto flex max-w-7xl gap-6 px-6 py-6">
        <Sidebar />
        <main className="flex-1 space-y-10">
          {/* Hero */}
          <section className="overflow-hidden rounded-3xl border border-border bg-gradient-to-br from-primary/10 via-card to-card p-10 shadow-sm">
            <div className="max-w-2xl">
              <span className="inline-block rounded-full bg-primary/15 px-3 py-1 text-xs font-medium uppercase tracking-wide text-primary">
                Fer&amp;Vic
              </span>
              <h1 className="mt-4 text-4xl font-bold tracking-tight text-foreground sm:text-5xl">
                Simple technology, intelligent support
              </h1>
              <p className="mt-4 text-base text-muted-foreground sm:text-lg">
                At Fer&amp;Vic, we select everyday tech products and provide intelligent
                support whenever you need help.
              </p>
              <Link
                to="/support"
                className="mt-6 inline-flex items-center justify-center rounded-full bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground shadow-sm transition hover:bg-primary/90"
              >
                Go to support
              </Link>
            </div>
          </section>

          {/* Products */}
          <section>
            <h2 className="mb-5 text-2xl font-semibold text-foreground">
              Featured products
            </h2>
            <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
              {products.map((p) => (
                <ProductCard key={p.name} {...p} />
              ))}
            </div>
          </section>

          {/* Trust */}
          <section className="rounded-2xl border border-border bg-card p-8 shadow-sm">
            <h2 className="text-2xl font-semibold text-foreground">
              Why choose Fer&amp;Vic?
            </h2>
            <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-2">
              {trustPoints.map((t) => (
                <div
                  key={t}
                  className="flex items-start gap-3 rounded-xl bg-secondary/50 p-4"
                >
                  <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary text-xs font-bold text-primary-foreground">
                    ✓
                  </span>
                  <span className="text-sm text-foreground">{t}</span>
                </div>
              ))}
            </div>
          </section>
        </main>
      </div>
    </div>
  );
}
