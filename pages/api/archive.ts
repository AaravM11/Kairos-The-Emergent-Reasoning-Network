import type { NextApiRequest, NextApiResponse } from "next";
import fs from "fs";
import path from "path";

const INDEX_PATH: string = path.join(process.cwd(), "output", "kairos_rounds_index.json");

function gatewayBase(): string {
  return (process.env.IPFS_GATEWAY_URL || "https://ipfs.io/ipfs").replace(/\/$/, "");
}

export default async function handler(req: NextApiRequest, res: NextApiResponse): Promise<void> {
  if (req.method !== "GET") {
    res.setHeader("Allow", ["GET"]);
    res.status(405).end(`Method ${req.method} Not Allowed`);
    return;
  }

  const cidRaw = req.query.cid;
  const cid: string | undefined = typeof cidRaw === "string" ? cidRaw.trim() : undefined;

  if (cid) {
    const url = `${gatewayBase()}/${cid}`;
    const ac = new AbortController();
    const timer = setTimeout(() => ac.abort(), 90_000);
    try {
      const r = await fetch(url, {
        headers: { Accept: "application/json" },
        signal: ac.signal,
      });
      if (!r.ok) {
        res.status(502).json({ error: `Gateway HTTP ${r.status} for ${url}` });
        return;
      }
      const data: unknown = await r.json();
      res.status(200).json({ cid, gateway_url: url, payload: data });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      res.status(502).json({ error: msg });
    } finally {
      clearTimeout(timer);
    }
    return;
  }

  try {
    const raw = fs.readFileSync(INDEX_PATH, "utf-8");
    const parsed: unknown = JSON.parse(raw);
    res.status(200).json(parsed);
  } catch {
    res.status(200).json({ rounds: [] });
  }
}
