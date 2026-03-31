import type { NextApiRequest, NextApiResponse } from "next";
import { spawn } from "child_process";

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
    const result = await runMarketplaceRound(payload);
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
    const proc = spawn("python3", ["scripts/run_marketplace_round.py"]);
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
      if (code !== 0) {
        return reject(new Error(stderr || `Process exited with code ${code}`));
      }
      try {
        resolve(JSON.parse(stdout));
      } catch {
        reject(new Error("Invalid JSON returned by Python marketplace runner"));
      }
    });

    proc.stdin.write(payload);
    proc.stdin.end();
  });
}