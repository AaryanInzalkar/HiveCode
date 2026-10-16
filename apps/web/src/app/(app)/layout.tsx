"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30000,
      retry: 3,
    },
  },
});

function TopBar() {
  const router = useRouter();
  const [user, setUser] = useState<{ github_login: string; avatar_url: string } | null>(null);

  useEffect(() => {
    fetch("/api/v1/auth/me")
      .then((res) => {
        if (res.ok) return res.json();
        throw new Error("Not authenticated");
      })
      .then((data) => setUser(data.user))
      .catch(() => router.push("/login"));
  }, [router]);

  const handleLogout = async () => {
    await fetch("/api/v1/auth/logout", { method: "POST" });
    router.push("/login");
  };

  return (
    <header className="sticky top-0 z-50 border-b border-border bg-background/95 backdrop-blur">
      <div className="flex h-14 items-center justify-between px-4">
        <div className="flex items-center gap-6">
          <Link href="/tasks" className="text-lg font-semibold tracking-tight">
            HiveCode
          </Link>
          <nav className="flex items-center gap-4">
            <Link
              href="/tasks"
              className="text-sm text-muted-foreground hover:text-foreground"
            >
              Tasks
            </Link>
            <Link
              href="/repositories"
              className="text-sm text-muted-foreground hover:text-foreground"
            >
              Repositories
            </Link>
          </nav>
        </div>

        <div className="flex items-center gap-4">
          {user && (
            <>
              <span className="text-sm text-muted-foreground">{user.github_login}</span>
              <button
                onClick={handleLogout}
                className="text-sm text-muted-foreground hover:text-foreground"
              >
                Sign out
              </button>
            </>
          )}
        </div>
      </div>
    </header>
  );
}

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen">
        <TopBar />
        <main className="container mx-auto max-w-6xl px-4 py-8">{children}</main>
      </div>
    </QueryClientProvider>
  );
}
