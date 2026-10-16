"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

type Repository = {
  id: string;
  full_name: string;
  default_branch: string;
  language: string | null;
};

export default function RepositoriesPage() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["repositories"],
    queryFn: async () => {
      const res = await fetch("/api/v1/repositories");
      if (!res.ok) throw new Error("Failed to fetch repositories");
      return res.json();
    },
  });

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="skeleton h-8 w-48" />
        {[1, 2, 3].map((i) => (
          <div key={i} className="skeleton h-24 w-full" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-md border border-red-500/20 bg-red-500/10 p-4">
        <p className="text-sm text-red-400">Failed to load repositories</p>
        <button
          onClick={() => refetch()}
          className="mt-2 text-sm text-red-300 underline"
        >
          Retry
        </button>
      </div>
    );
  }

  const repos: Repository[] = data?.repositories || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Repositories</h1>
        <button
          onClick={() => refetch()}
          className="rounded-md border border-border px-3 py-1.5 text-sm hover:bg-muted"
        >
          Refresh
        </button>
      </div>

      {repos.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <p className="text-lg font-medium">No repositories yet</p>
          <p className="mt-1 text-sm text-muted-foreground">
            Install the HiveCode GitHub App to get started
          </p>
          <a
            href="https://github.com/apps/hivecode/installations/new"
            target="_blank"
            rel="noopener noreferrer"
            className="mt-4 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            Install GitHub App
          </a>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {repos.map((repo) => (
            <div
              key={repo.id}
              className="rounded-lg border border-border bg-card p-4"
            >
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-medium">{repo.full_name}</h3>
                  <p className="mt-1 text-sm text-muted-foreground">
                    {repo.language && (
                      <span className="mr-2 inline-block h-2 w-2 rounded-full bg-green-500" />
                    )}
                    {repo.language || "Unknown"} · {repo.default_branch}
                  </p>
                </div>
                <Link
                  href={`/tasks/new?repository=${repo.id}`}
                  className="rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90"
                >
                  New Task
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
