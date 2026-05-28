import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { Header } from "@/components/Header";
import { Sidebar } from "@/components/Sidebar";
import { SupportForm } from "@/components/SupportForm";
import { ChatWindow } from "@/components/ChatWindow";

export const Route = createFileRoute("/support")({
  head: () => ({
    meta: [
      { title: "Support — Fer&Vic" },
      {
        name: "description",
        content: "Get intelligent customer support for your Fer&Vic products.",
      },
    ],
  }),
  component: SupportPage,
});

function SupportPage() {
  const [selection, setSelection] = useState<{
    domain: string;
    subdomain: string;
    product: string;
  } | null>(null);
  const [resetKey, setResetKey] = useState(0);

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <div className="mx-auto flex max-w-7xl gap-6 px-6 py-6">
        <Sidebar />
        <main className="flex flex-1 flex-col">
          {!selection ? (
            <div className="flex flex-1 items-start justify-center py-8">
              <SupportForm onSubmit={setSelection} />
            </div>
          ) : (
            <ChatWindow
              key={resetKey}
              selection={selection}
              onReset={() => {
                setSelection(null);
                setResetKey((k) => k + 1);
              }}
            />
          )}
        </main>
      </div>
    </div>
  );
}
