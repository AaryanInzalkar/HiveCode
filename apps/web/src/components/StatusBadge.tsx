import { clsx } from "clsx";

const outcomeConfig: Record<string, { color: string; icon: string; label: string }> = {
  verified: { color: "bg-green-500/10 text-green-400", icon: "✓", label: "Verified" },
  failed: { color: "bg-red-500/10 text-red-400", icon: "✗", label: "Failed" },
  blocked: { color: "bg-amber-500/10 text-amber-400", icon: "⚠", label: "Blocked" },
  partially_verified: { color: "bg-blue-500/10 text-blue-400", icon: "◐", label: "Partially verified" },
  running: { color: "bg-gray-500/10 text-gray-400", icon: "◌", label: "Running" },
  queued: { color: "bg-gray-500/10 text-gray-400", icon: "◷", label: "Queued" },
  awaiting_approval: { color: "bg-amber-500/10 text-amber-400", icon: "⏸", label: "Awaiting approval" },
  cancelled: { color: "bg-gray-500/10 text-gray-400", icon: "⊘", label: "Cancelled" },
};

export function StatusBadge({ outcome, stage }: { outcome: string | null; stage?: string | null }) {
  const key = outcome || (stage === "running" ? "running" : stage || "queued");
  const config = outcomeConfig[key] || { color: "bg-gray-500/10 text-gray-400", icon: "?", label: key };

  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium",
        config.color
      )}
    >
      {config.icon} {config.label}
    </span>
  );
}

const checkStatusConfig: Record<string, { color: string; icon: string; label: string }> = {
  passed: { color: "bg-green-500/10 text-green-400", icon: "✓", label: "Passed" },
  failed: { color: "bg-red-500/10 text-red-400", icon: "✗", label: "Failed" },
  error: { color: "bg-orange-500/10 text-orange-400", icon: "⚠", label: "Error" },
  timed_out: { color: "bg-amber-500/10 text-amber-400", icon: "⏱", label: "Timed out" },
  skipped: { color: "bg-gray-500/10 text-gray-400", icon: "⊘", label: "Skipped" },
  unavailable: { color: "bg-gray-500/10 text-gray-400", icon: "?", label: "Unavailable" },
  cancelled: { color: "bg-gray-500/10 text-gray-400", icon: "⊘", label: "Cancelled" },
};

export function CheckStatusBadge({ status }: { status: string }) {
  const config = checkStatusConfig[status] || { color: "bg-gray-500/10 text-gray-400", icon: "?", label: status };

  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium",
        config.color
      )}
    >
      {config.icon} {config.label}
    </span>
  );
}
