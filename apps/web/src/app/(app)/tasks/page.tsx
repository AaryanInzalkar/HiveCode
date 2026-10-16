"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";

type Task = {
  id: string;
  title: string;
  state: string;
  outcome: string | null;
  repair_attempts_used: number;
  created_at: string;
  repository_id: string;
};

const outcomeColors: Record<string, string> = {
  verified: "bg-green-500/10 text-green-400",
  failed: "bg-red-500/10 text-red-400",
  blocked: "bg-amber-500/10 text-amber-400",
  partially_verified: "bg-blue-500/10 text-blue-400",
};

const outcomeIcons: Record<string, string> = {
  verified: "✓",
  failed: "✗",
  blocked: "⚠",
  partially_verified: "◐",
};

export default function TasksPage() {
  const router = useRouter();
  const { data, isLoading, error } = useQuery({
    queryKey: ["tasks"],
    queryFn: async () => {
      const res = await fetch("/api/v1/tasks");
      if (!res.ok) throw new Error("Failed to fetch tasks");
      return res.json();
    },
  });

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="skeleton h-8 w-48" />
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="skeleton h-20 w-full" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-md border border-red-500/20 bg-red-500/10 p-4">
        <p className="text-sm text-red-400">Failed to load tasks</p>
        <button
          onClick={() => router.refresh()}
          className="mt-2 text-sm text-red-300 underline"
        >
          Retry
        </button>
      </div>
    );
  }

  const tasks: Task[] = data?.tasks || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Tasks</h1>
        <Link
          href="/tasks/new"
          className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          + New Task
        </Link>
      </div>

      {tasks.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <p className="text-lg font-medium">No tasks yet</p>
          <p className="mt-1 text-sm text-muted-foreground">
            Submit your first task to get started
          </p>
          <Link
            href="/tasks/new"
            className="mt-4 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            + New Task
          </Link>
        </div>
      ) : (
        <div className="space-y-3">
          {tasks.map((task) => (
            <Link
              key={task.id}
              href={`/tasks/${task.id}`}
              className="block rounded-lg border border-border bg-card p-4 hover:border-primary/50"
            >
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-medium">{task.title}</h3>
                  <p className="mt-1 text-sm text-muted-foreground">
                    {new Date(task.created_at).toLocaleString()}
                  </p>
                </div>
                {task.outcome && (
                  <span
                    className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ${outcomeColors[task.outcome] || "bg-gray-500/10 text-gray-400"}`}
                  >
                    {outcomeIcons[task.outcome]} {task.outcome.replace("_", " ")}
                  </span>
                )}
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
