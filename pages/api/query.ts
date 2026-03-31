import type { NextApiRequest, NextApiResponse } from "next";
import { spawn } from "child_process";
import path from "path";

/** Prefer venv: KAIROS_PYTHON=.venv/bin/python in .env so `openai` is found. */
function pythonExecutable(): string {
  return process.env.KAIROS_PYTHON || process.env.PYTHON_PATH || "python3";
}

/**
 * Python may print warnings / logs to stdout before the final JSON line.
 * Prefer the last parseable JSON object in the buffer.
 */
function parsePythonStdoutJson(raw: string): Record<string, unknown> | null {
  const t = raw.trim();
  if (!t) return null;
  const tryParse = (s: string): Record<string, unknown> | null => {
    try {
      const v = JSON.parse(s) as unknown;
      if (v !== null && typeof v === "object" && !Array.isArray(v)) {
        return v as Record<string, unknown>;
      }
    } catch {
      /* ignore */
    }
    return null;
  };
  const direct = tryParse(t);
  if (direct) return direct;
  const lines = t.split(/\n/);
  for (let i = lines.length - 1; i >= 0; i--) {
    const line = lines[i].trim();
    if (!line.startsWith("{")) continue;
    const fromLine = tryParse(line);
    if (fromLine) return fromLine;
  }
  const lastOpen = t.lastIndexOf("{");
  if (lastOpen >= 0) {
    let depth = 0;
    for (let i = lastOpen; i < t.length; i++) {
      const c = t[i];
      if (c === "{") depth++;
      else if (c === "}") {
        depth--;
        if (depth === 0) {
          const slice = tryParse(t.slice(lastOpen, i + 1));
          if (slice) return slice;
          break;
        }
      }
    }
  }
  return null;
}

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== "POST") {
    res.setHeader("Allow", ["POST"]);
    return res.status(405).end(`Method ${req.method} Not Allowed`);
  }

  const { query, openai_key, alignment_profile } = req.body || {};
  if (!query) {
    return res.status(400).json({ error: "Missing required query" });
  }

  try {
    const payload = JSON.stringify({
      query,
      openai_key: openai_key || process.env.OPENAI_API_KEY,
      alignment_profile,
      run_validation: true,
      kg_path: "output/knowledge_graph.json",
    });
    const result = (await runMarketplaceRound(payload)) as { error?: string };
    if (result.error) {
      return res.status(500).json(result);
    }
    return res.status(200).json(result);
  } catch (err: any) {
    return res.status(500).json({ error: err?.message || "Marketplace run failed" });
  }
}

function runMarketplaceRound(payload: string): Promise<any> {
  return new Promise((resolve, reject) => {
    const proc = spawn(pythonExecutable(), [path.join("scripts", "run_marketplace_round.py")], {
      cwd: process.cwd(),
      env: process.env,
    });
    let stdout = "";
    let stderr = "";

    proc.stdout.on("data", (chunk) => {
      stdout += chunk.toString();
    });
    proc.stderr.on("data", (chunk) => {
      stderr += chunk.toString();
    });
    proc.on("error", reject);
    proc.on("close", (code) => {
      const parsed = parsePythonStdoutJson(stdout);
      if (parsed !== null) {
        resolve(parsed);
        return;
      }
      const headOut = stdout.trim().slice(0, 800);
      const headErr = stderr.trim().slice(0, 800);
      if (code !== 0) {
        reject(
          new Error(
            headErr ||
              headOut ||
              `Python exited with code ${code} (no JSON on stdout; check stderr above)`
          )
        );
        return;
      }
      reject(
        new Error(
          `Invalid JSON from marketplace runner. stdout (first 800 chars): ${headOut || "(empty)"} stderr: ${headErr || "(empty)"}`
        )
      );
    });

    proc.stdin.write(payload);
    proc.stdin.end();
  });
}