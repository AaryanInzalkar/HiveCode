"use client";

import { clsx } from "clsx";

type DiffLine = {
  type: "add" | "del" | "context" | "hunk";
  content: string;
  lineNumber?: number;
};

export function DiffView({ diff }: { diff: string }) {
  const lines = parseDiff(diff);

  return (
    <div className="overflow-x-auto rounded-md border border-border bg-[#1a1a1e] p-4">
      <pre className="text-xs">
        {lines.map((line, i) => (
          <div
            key={i}
            className={clsx(
              "flex",
              line.type === "add" && "diff-add",
              line.type === "del" && "diff-del",
              line.type === "hunk" && "diff-hunk"
            )}
          >
            <span className="mr-4 inline-block w-8 select-none text-right text-muted-foreground">
              {line.lineNumber || ""}
            </span>
            <span>{line.content}</span>
          </div>
        ))}
      </pre>
    </div>
  );
}

function parseDiff(diff: string): DiffLine[] {
  const lines: DiffLine[] = [];
  let oldLine = 0;
  let newLine = 0;

  for (const line of diff.split("\n")) {
    if (line.startsWith("@@")) {
      const match = line.match(/@@ -(\d+),\d+ \+(\d+),\d+ @@/);
      if (match) {
        oldLine = parseInt(match[1]);
        newLine = parseInt(match[2]);
      }
      lines.push({ type: "hunk", content: line });
    } else if (line.startsWith("+") && !line.startsWith("+++")) {
      lines.push({ type: "add", content: line, lineNumber: newLine++ });
    } else if (line.startsWith("-") && !line.startsWith("---")) {
      lines.push({ type: "del", content: line, lineNumber: oldLine++ });
    } else if (line.startsWith(" ")) {
      lines.push({ type: "context", content: line, lineNumber: newLine++ });
      oldLine++;
    }
  }

  return lines;
}
