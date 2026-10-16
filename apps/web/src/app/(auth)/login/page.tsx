"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const router = useRouter();
  const [status, setStatus] = useState<{
    authenticated: boolean;
    app_installed: boolean;
  } | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch("/api/v1/auth/status")
      .then((res) => res.json())
      .then((data) => {
        setStatus(data);
        if (data.authenticated) {
          router.push("/tasks");
        }
      })
      .catch(() => setStatus({ authenticated: false, app_installed: true }));
  }, [router]);

  const handleSignIn = () => {
    setLoading(true);
    window.location.href = "/api/v1/auth/github/login";
  };

  if (!status) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="skeleton h-8 w-48" />
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="w-full max-w-md space-y-8 p-8">
        <div className="text-center">
          <h1 className="text-3xl font-semibold tracking-tight">HiveCode</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Don&apos;t stop when code changes.
            <br />
            Stop when the fix is verified.
          </p>
        </div>

        <div className="space-y-4">
          <button
            onClick={handleSignIn}
            disabled={loading}
            className="flex w-full items-center justify-center gap-2 rounded-md bg-[#24292F] px-4 py-3 text-sm font-medium text-white hover:bg-[#2f363d] disabled:opacity-50"
          >
            {loading ? (
              <span>Redirecting to GitHub...</span>
            ) : (
              <>
                <svg className="h-5 w-5" viewBox="0 0 16 16" fill="currentColor">
                  <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z" />
                </svg>
                Sign in with GitHub
              </>
            )}
          </button>

          {!status.app_installed && (
            <div className="rounded-md border border-amber-500/20 bg-amber-500/10 p-4 text-center">
              <p className="text-sm text-amber-400">
                HiveCode needs the GitHub App to access your repositories.
              </p>
              <a
                href="https://github.com/apps/hivecode/installations/new"
                target="_blank"
                rel="noopener noreferrer"
                className="mt-2 inline-block text-sm text-amber-300 underline hover:text-amber-200"
              >
                Install the GitHub App
              </a>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
