"use client";

import { useState, useEffect } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

type JobStatus =
  | "pending"
  | "script"
  | "video_gen"
  | "voice"
  | "assembly"
  | "thumbnail"
  | "upload"
  | "completed"
  | "failed";

interface MatchupRequest {
  player1: string;
  player2: string;
  setting: string;
  game_format: string;
}

interface JobState {
  job_id: string;
  request: MatchupRequest;
  status: JobStatus;
  video_path?: string;
  thumbnail_path?: string;
  youtube_url?: string;
  error?: string;
  title?: string;
  description?: string;
}

const STEPS: { key: JobStatus; label: string }[] = [
  { key: "pending", label: "Queued" },
  { key: "script", label: "Script" },
  { key: "video_gen", label: "Clips" },
  { key: "voice", label: "Voice" },
  { key: "assembly", label: "Assembly" },
  { key: "thumbnail", label: "Thumbnail" },
  { key: "upload", label: "Upload" },
  { key: "completed", label: "Done" },
  { key: "failed", label: "Failed" },
];

const LEGAL_DISCLAIMER =
  "This tool generates fictional, AI-simulated content for entertainment only. It does not represent real events or endorsements. Do not use to impersonate or misrepresent any person. You are responsible for complying with applicable law and platform terms.";

export default function Home() {
  const [player1, setPlayer1] = useState("Michael Jordan");
  const [player2, setPlayer2] = useState("LeBron James");
  const [setting, setSetting] = useState("outdoor Chicago court");
  const [gameFormat, setGameFormat] = useState("1v1 to 21");
  const [running, setRunning] = useState(false);
  const [asyncMode, setAsyncMode] = useState(false);
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobState, setJobState] = useState<JobState | null>(null);
  const [polling, setPolling] = useState(false);
  const [ackLegal, setAckLegal] = useState(false);
  const [showLegal, setShowLegal] = useState(false);

  const runPipeline = async () => {
    setRunning(true);
    setResult(null);
    setJobId(null);
    setJobState(null);
    const body: MatchupRequest = {
      player1,
      player2,
      setting,
      game_format: gameFormat,
    };
    try {
      const url = `${API_BASE}/api/matchup/run`;
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error((err as { detail?: string }).detail || "Request failed");
      }
      const data = await res.json();
      setResult(data);
    } catch (e) {
      setResult({ error: String(e) });
    } finally {
      setRunning(false);
    }
  };

  const runPipelineAsync = async () => {
    setRunning(true);
    setResult(null);
    setJobState(null);
    const body: MatchupRequest = {
      player1,
      player2,
      setting,
      game_format: gameFormat,
    };
    try {
      const url = `${API_BASE}/api/matchup/run-async`;
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error((err as { detail?: string }).detail || "Request failed");
      }
      const data = await res.json();
      setJobId((data as { job_id?: string }).job_id ?? null);
      setPolling(true);
    } catch (e) {
      setResult({ error: String(e) });
      setRunning(false);
    }
  };

  // Poll job status when jobId is set
  const pollJob = async () => {
    if (!jobId || !API_BASE) return;
    try {
      const res = await fetch(`${API_BASE}/api/jobs/${jobId}`);
      if (!res.ok) return;
      const data = await res.json();
      setJobState(data as JobState);
      if (data.status === "completed" || data.status === "failed") {
        setPolling(false);
        setRunning(false);
      }
    } catch {
      setPolling(false);
    }
  };

  useEffect(() => {
    if (!polling || !jobId) return;
    pollJob();
    const t = setInterval(pollJob, 2000);
    return () => clearInterval(t);
  }, [polling, jobId]);

  return (
    <main className="min-h-screen p-6 md:p-10">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-3xl font-bold text-goat-orange mb-1">
          GOAT Matchup Video Generator
        </h1>
        <p className="text-zinc-400 mb-4">
          Generate a full highlight video from a single matchup request.
        </p>

        {/* Legal / compliance notice */}
        <div className="mb-6 rounded-xl border border-amber-500/30 bg-amber-500/5 p-4">
          <button
            type="button"
            onClick={() => setShowLegal(!showLegal)}
            className="flex w-full items-center justify-between text-left text-sm font-medium text-amber-200"
          >
            Legal &amp; compliance notice
            <span className="text-amber-400">{showLegal ? "−" : "+"}</span>
          </button>
          {showLegal && (
            <p className="mt-2 text-xs text-zinc-400">{LEGAL_DISCLAIMER}</p>
          )}
          <label className="mt-3 flex cursor-pointer items-center gap-2 text-sm text-zinc-300">
            <input
              type="checkbox"
              checked={ackLegal}
              onChange={(e) => setAckLegal(e.target.checked)}
              className="rounded border-zinc-600 text-amber-500 focus:ring-amber-500"
            />
            I understand this creates fictional AI-simulated content and I will use it in compliance with applicable law and platform terms.
          </label>
        </div>

        <div className="bg-zinc-900/80 rounded-xl p-6 border border-zinc-800 space-y-4">
          <div>
            <label className="block text-sm text-zinc-400 mb-1">Player 1</label>
            <input
              type="text"
              value={player1}
              onChange={(e) => setPlayer1(e.target.value)}
              className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-white placeholder-zinc-500 focus:ring-2 focus:ring-amber-500/50 focus:border-amber-500"
              placeholder="Michael Jordan"
            />
          </div>
          <div>
            <label className="block text-sm text-zinc-400 mb-1">Player 2</label>
            <input
              type="text"
              value={player2}
              onChange={(e) => setPlayer2(e.target.value)}
              className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-white placeholder-zinc-500 focus:ring-2 focus:ring-amber-500/50 focus:border-amber-500"
              placeholder="LeBron James"
            />
          </div>
          <div>
            <label className="block text-sm text-zinc-400 mb-1">Setting</label>
            <input
              type="text"
              value={setting}
              onChange={(e) => setSetting(e.target.value)}
              className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-white placeholder-zinc-500 focus:ring-2 focus:ring-amber-500/50 focus:border-amber-500"
              placeholder="outdoor Chicago court"
            />
          </div>
          <div>
            <label className="block text-sm text-zinc-400 mb-1">
              Game format
            </label>
            <input
              type="text"
              value={gameFormat}
              onChange={(e) => setGameFormat(e.target.value)}
              className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-white placeholder-zinc-500 focus:ring-2 focus:ring-amber-500/50 focus:border-amber-500"
              placeholder="1v1 to 21"
            />
          </div>

          <div className="flex items-center gap-2 pt-2">
            <input
              type="checkbox"
              id="async"
              checked={asyncMode}
              onChange={(e) => setAsyncMode(e.target.checked)}
              className="rounded border-zinc-600 text-amber-500 focus:ring-amber-500"
            />
            <label htmlFor="async" className="text-sm text-zinc-400">
              Run in background (returns immediately, poll for status)
            </label>
          </div>

          <div className="flex gap-3 pt-2">
            <button
              onClick={asyncMode ? runPipelineAsync : runPipeline}
              disabled={running || !ackLegal}
              className="px-5 py-2.5 bg-amber-500 hover:bg-amber-400 disabled:bg-zinc-600 disabled:cursor-not-allowed text-zinc-950 font-semibold rounded-lg transition"
            >
              {running ? "Running…" : "Generate video"}
            </button>
            {!ackLegal && (
              <span className="self-center text-xs text-zinc-500">
                Acknowledge the notice above to continue.
              </span>
            )}
          </div>
        </div>

        {/* Progress for async job */}
        {jobState && (
          <div className="mt-6 bg-zinc-900/80 rounded-xl p-6 border border-zinc-800">
            <h2 className="text-lg font-semibold text-zinc-200 mb-3">
              Job {jobState.job_id}
            </h2>
            <div className="flex flex-wrap gap-2 mb-3">
              {STEPS.map(({ key, label }) => (
                <span
                  key={key}
                  className={`px-2 py-1 rounded text-sm ${
                    jobState.status === key
                      ? "bg-amber-500/20 text-amber-400"
                      : STEPS.findIndex((s) => s.key === jobState.status) >
                          STEPS.findIndex((s) => s.key === key)
                      ? "bg-zinc-700 text-zinc-300"
                      : "bg-zinc-800 text-zinc-500"
                  }`}
                >
                  {label}
                </span>
              ))}
            </div>
            {jobState.error && (
              <p className="text-red-400 text-sm">{jobState.error}</p>
            )}
            {jobState.status === "completed" && (
              <div className="text-sm text-zinc-300 space-y-1">
                {jobState.video_path && (
                  <p>Video: {jobState.video_path}</p>
                )}
                {jobState.youtube_url && (
                  <a
                    href={jobState.youtube_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-amber-400 hover:underline"
                  >
                    Watch on YouTube
                  </a>
                )}
              </div>
            )}
          </div>
        )}

        {/* Sync result */}
        {result && !jobState && (
          <div className="mt-6 bg-zinc-900/80 rounded-xl p-6 border border-zinc-800">
            <h2 className="text-lg font-semibold text-zinc-200 mb-3">
              Result
            </h2>
            {"error" in result ? (
              <p className="text-red-400">{(result as { error: string }).error}</p>
            ) : (
              <pre className="text-sm text-zinc-300 whitespace-pre-wrap break-words">
                {JSON.stringify(result, null, 2)}
              </pre>
            )}
          </div>
        )}
      </div>
    </main>
  );
}
