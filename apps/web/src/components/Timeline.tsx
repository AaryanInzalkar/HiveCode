"use client";

import { clsx } from "clsx";

type TimelineEvent = {
  seq: number;
  type: string;
  stage?: string | null;
  attempt_no?: number | null;
  data?: Record<string, unknown>;
  created_at: string;
};

export function Timeline({ events }: { events: TimelineEvent[] }) {
  if (events.length === 0) {
    return <p className="text-sm text-muted-foreground">No events yet</p>;
  }

  return (
    <div className="space-y-0">
      {events.map((event, i) => (
        <div key={event.seq} className="flex items-start gap-3">
          <div className="flex flex-col items-center">
            <div
              className={clsx(
                "mt-1 h-3 w-3 rounded-full",
                getEventColor(event.type)
              )}
            />
            {i < events.length - 1 && (
              <div className="h-full w-0.5 bg-border" />
            )}
          </div>
          <div className="pb-4">
            <p className="text-sm font-medium">
              {event.type.replace(/_/g, " ")}
            </p>
            {event.stage && (
              <p className="text-xs text-muted-foreground">
                Stage: {event.stage}
              </p>
            )}
            <p className="text-xs text-muted-foreground">
              {new Date(event.created_at).toLocaleTimeString()}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
}

function getEventColor(type: string): string {
  if (type.includes("complete") || type.includes("verified") || type.includes("passed")) {
    return "bg-green-500";
  }
  if (type.includes("fail") || type.includes("error")) {
    return "bg-red-500";
  }
  if (type.includes("blocked") || type.includes("approval")) {
    return "bg-amber-500";
  }
  return "bg-gray-500";
}
