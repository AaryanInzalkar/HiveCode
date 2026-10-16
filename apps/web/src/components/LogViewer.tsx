"use client";

import { clsx } from "clsx";

type LogViewerProps = {
  content: string;
  truncated?: boolean;
  maxHeight?: number;
};

export function LogViewer({ content, truncated = false, maxHeight = 400 }: LogViewerProps) {
  return (
    <div className="space-y-2">
      <div
        className="overflow-auto rounded-md border border-border bg-[#1a1a1e] p-4"
        style={{ maxHeight }}
      >
        <pre className="text-xs text-foreground">
          {content}
        </pre>
      </div>
      {truncated && (
        <p className="text-xs text-amber-400">
          Output truncated (showing last portion of log)
        </p>
      )}
    </div>
  );
}
