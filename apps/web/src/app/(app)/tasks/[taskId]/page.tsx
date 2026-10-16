"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import Link from "next/link";

type TaskDetail = {
  id: string;
  title: string;
  objective: string;
  state: string;
  stage: string | null;
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

const tabs = ["Overview", "Timeline", "Attempts", "Checks", "Review", "Report", "Approvals"];

export default function TaskDetailPage() {
  const params = useParams();
  const router = useRouter();
  const taskId = params.taskId as string;
  const [activeTab, setActiveTab] = useState("Overview");

  const { data: task, isLoading } = useQuery({
    queryKey: ["task", taskId],
    queryFn: async () => {
      const res = await fetch(`/api/v1/tasks/${taskId}`);
      if (!res.ok) throw new Error("Failed to fetch task");
      return res.json();
    },
    refetchInterval: (query) => {
      const state = query.state.data?.state;
      return state === "finished" || state === "cancelled" ? false : 3000;
    },
  });

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="skeleton h-8 w-96" />
        <div className="skeleton h-4 w-48" />
        <div className="skeleton h-64 w-full" />
      </div>
    );
  }

  if (!task) {
    return (
      <div className="text-center py-16">
        <p className="text-lg">Task not found</p>
        <Link href="/tasks" className="mt-2 inline-block text-sm text-primary hover:underline">
          Back to tasks
        </Link>
      </div>
    );
  }

  const isTerminal = task.state === "finished" || task.state === "cancelled";

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <Link href="/tasks" className="text-sm text-muted-foreground hover:text-foreground">
          ← Back to tasks
        </Link>
        <div className="mt-2 flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-semibold">{task.title}</h1>
            <p className="mt-1 text-sm text-muted-foreground">
              {new Date(task.created_at).toLocaleString()}
            </p>
          </div>
          {task.outcome && (
            <span
              className={`inline-flex items-center rounded-full px-3 py-1 text-sm font-medium ${outcomeColors[task.outcome] || "bg-gray-500/10 text-gray-400"}`}
            >
              {task.outcome.replace("_", " ")}
            </span>
          )}
          {task.state === "running" && task.stage && (
            <span className="inline-flex items-center gap-2 rounded-full bg-gray-500/10 px-3 py-1 text-sm text-gray-400">
              <span className="h-2 w-2 animate-pulse rounded-full bg-gray-400" />
              {task.stage}
            </span>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-border">
        <nav className="flex gap-1 overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`whitespace-nowrap border-b-2 px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === tab
                  ? "border-primary text-foreground"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              }`}
            >
              {tab}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab content */}
      <div className="min-h-[400px]">
        {activeTab === "Overview" && <OverviewTab task={task} />}
        {activeTab === "Timeline" && <TimelineTab taskId={taskId} />}
        {activeTab === "Attempts" && <AttemptsTab taskId={taskId} />}
        {activeTab === "Checks" && <ChecksTab taskId={taskId} />}
        {activeTab === "Review" && <ReviewTab taskId={taskId} />}
        {activeTab === "Report" && <ReportTab taskId={taskId} />}
        {activeTab === "Approvals" && <ApprovalsTab taskId={taskId} />}
      </div>
    </div>
  );
}

function OverviewTab({ task }: { task: TaskDetail }) {
  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-sm font-medium text-muted-foreground">Objective</h3>
        <p className="mt-1 text-sm">{task.objective}</p>
      </div>
      <div className="grid grid-cols-2 gap-4 text-sm">
        <div>
          <span className="text-muted-foreground">State:</span> {task.state}
        </div>
        <div>
          <span className="text-muted-foreground">Stage:</span> {task.stage || "—"}
        </div>
        <div>
          <span className="text-muted-foreground">Attempts:</span> {task.repair_attempts_used}/4
        </div>
        <div>
          <span className="text-muted-foreground">Outcome:</span> {task.outcome || "—"}
        </div>
      </div>
    </div>
  );
}

function TimelineTab({ taskId }: { taskId: string }) {
  const { data } = useQuery({
    queryKey: ["events", taskId],
    queryFn: async () => {
      const res = await fetch(`/api/v1/events?task_id=${taskId}&after_seq=0`);
      if (!res.ok) throw new Error("Failed to fetch events");
      return res.json();
    },
    refetchInterval: 3000,
  });

  const events = data?.events || [];

  if (events.length === 0) {
    return <p className="text-sm text-muted-foreground">No events yet</p>;
  }

  return (
    <div className="space-y-1">
      {events.map((event: { seq: number; type: string; created_at: string }) => (
        <div key={event.seq} className="flex items-start gap-3 py-2">
          <div className="mt-1.5 h-2 w-2 rounded-full bg-primary" />
          <div>
            <p className="text-sm font-medium">{event.type.replace(/_/g, " ")}</p>
            <p className="text-xs text-muted-foreground">
              {new Date(event.created_at).toLocaleTimeString()}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
}

function AttemptsTab({ taskId }: { taskId: string }) {
  return (
    <div className="flex items-center justify-center py-16 text-sm text-muted-foreground">
      Attempt details will appear here after the first patch is generated.
    </div>
  );
}

function ChecksTab({ taskId }: { taskId: string }) {
  return (
    <div className="flex items-center justify-center py-16 text-sm text-muted-foreground">
      Check results will appear here after validation runs.
    </div>
  );
}

function ReviewTab({ taskId }: { taskId: string }) {
  return (
    <div className="flex items-center justify-center py-16 text-sm text-muted-foreground">
      Review findings will appear here after the independent review completes.
    </div>
  );
}

function ReportTab({ taskId }: { taskId: string }) {
  return (
    <div className="flex items-center justify-center py-16 text-sm text-muted-foreground">
      The verification report will appear here when the task completes.
    </div>
  );
}

function ApprovalsTab({ taskId }: { taskId: string }) {
  return (
    <div className="flex items-center justify-center py-16 text-sm text-muted-foreground">
      No approvals required for this task.
    </div>
  );
}
