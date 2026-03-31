import type { NextApiRequest, NextApiResponse } from "next";
import { spawn } from "child_process";
import path from "path";

/** Prefer venv: KAIROS_PYTHON=.venv/bin/python in .env so `openai` is found. */
function pythonExecutable(): string {
  return process.env.KAIROS_PYTHON || process.env.PYTHON_PATH || "python3";
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
      const trimmed = stdout.trim();
      let parsed: unknown = null;
      if (trimmed) {
        try {
          parsed = JSON.parse(trimmed);
        } catch {
          /* ignore */
        }
      }
      // Python prints JSON to stdout even on sys.exit(1) (e.g. uncaught exception in main).
      if (parsed !== null && typeof parsed === "object") {
        resolve(parsed as Record<string, unknown>);
        return;
      }
      if (code !== 0) {
        reject(new Error(stderr.trim() || trimmed || `Python exited with code ${code}`));
        return;
      }
      reject(new Error("Invalid JSON returned by Python marketplace runner"));
    });

    proc.stdin.write(payload);
    proc.stdin.end();
  });
}