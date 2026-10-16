"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";

export default function NewTaskPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const preselectedRepo = searchParams.get("repository") || "";

  const [form, setForm] = useState({
    repository_id: preselectedRepo,
    base_ref: "main",
    title: "",
    objective: "",
    delivery_mode: "pr",
  });
  const [criteria, setCriteria] = useState<string[]>([""]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      const res = await fetch("/api/v1/tasks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...form,
          acceptance_criteria: criteria.filter((c) => c.trim()),
          scope: {},
        }),
      });

      if (res.status === 202) {
        const data = await res.json();
        router.push(`/tasks/${data.task_id}`);
      } else {
        const err = await res.json();
        setError(err.detail || "Failed to create task");
      }
    } catch (err) {
      setError("Network error");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="mx-auto max-w-2xl space-y-8">
      <div>
        <Link href="/tasks" className="text-sm text-muted-foreground hover:text-foreground">
          ← Back to tasks
        </Link>
        <h1 className="mt-2 text-2xl font-semibold">New Task</h1>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Repository */}
        <div className="space-y-2">
          <label className="text-sm font-medium">Repository</label>
          <input
            type="text"
            value={form.repository_id}
            onChange={(e) => setForm({ ...form, repository_id: e.target.value })}
            placeholder="owner/repo"
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            required
          />
        </div>

        {/* Base ref */}
        <div className="space-y-2">
          <label className="text-sm font-medium">Base branch or commit</label>
          <input
            type="text"
            value={form.base_ref}
            onChange={(e) => setForm({ ...form, base_ref: e.target.value })}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          />
        </div>

        {/* Title */}
        <div className="space-y-2">
          <label className="text-sm font-medium">Title</label>
          <input
            type="text"
            value={form.title}
            onChange={(e) => setForm({ ...form, title: e.target.value })}
            placeholder="Fix duplicate orders in GET /orders"
            maxLength={200}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            required
          />
        </div>

        {/* Objective */}
        <div className="space-y-2">
          <label className="text-sm font-medium">Describe the issue</label>
          <textarea
            value={form.objective}
            onChange={(e) => setForm({ ...form, objective: e.target.value })}
            placeholder="When listing orders, duplicates appear in the response..."
            rows={5}
            maxLength={5000}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            required
          />
        </div>

        {/* Acceptance criteria */}
        <div className="space-y-2">
          <label className="text-sm font-medium">Acceptance criteria</label>
          {criteria.map((c, i) => (
            <div key={i} className="flex gap-2">
              <input
                type="text"
                value={c}
                onChange={(e) => {
                  const newCriteria = [...criteria];
                  newCriteria[i] = e.target.value;
                  setCriteria(newCriteria);
                }}
                placeholder="test_list_orders_no_duplicates passes"
                className="flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm"
              />
              {criteria.length > 1 && (
                <button
                  type="button"
                  onClick={() => setCriteria(criteria.filter((_, j) => j !== i))}
                  className="rounded-md border border-border px-3 text-sm hover:bg-muted"
                >
                  ✕
                </button>
              )}
            </div>
          ))}
          <button
            type="button"
            onClick={() => setCriteria([...criteria, ""])}
            className="text-sm text-primary hover:underline"
          >
            + Add criterion
          </button>
        </div>

        {/* Delivery mode */}
        <div className="space-y-2">
          <label className="text-sm font-medium">Delivery</label>
          <div className="flex gap-4">
            <label className="flex items-center gap-2">
              <input
                type="radio"
                name="delivery"
                value="pr"
                checked={form.delivery_mode === "pr"}
                onChange={() => setForm({ ...form, delivery_mode: "pr" })}
              />
              <span className="text-sm">Create pull request</span>
            </label>
            <label className="flex items-center gap-2">
              <input
                type="radio"
                name="delivery"
                value="report"
                checked={form.delivery_mode === "report"}
                onChange={() => setForm({ ...form, delivery_mode: "report" })}
              />
              <span className="text-sm">Report only</span>
            </label>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="rounded-md border border-red-500/20 bg-red-500/10 p-3 text-sm text-red-400">
            {error}
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center gap-4">
          <Link
            href="/tasks"
            className="rounded-md border border-border px-4 py-2 text-sm hover:bg-muted"
          >
            Cancel
          </Link>
          <button
            type="submit"
            disabled={submitting}
            className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
          >
            {submitting ? "Submitting..." : "Submit Task"}
          </button>
        </div>
      </form>
    </div>
  );
}
