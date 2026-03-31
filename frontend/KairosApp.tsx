import React, { useState, ChangeEvent, useRef } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@radix-ui/react-label";
import {
  Upload,
  Sparkles,
  Share2,
  Database,
  GitBranch,
  Trophy,
  Shield,
  ExternalLink,
  AlertCircle,
} from "lucide-react";

const IPFS_GATEWAY: string = "https://ipfs.io/ipfs";

interface ReasoningResult {
  conclusion?: string;
  answer?: string;
  [key: string]: unknown;
}

interface ValidationResult {
  [key: string]: unknown;
}

interface CompetitionRow {
  module_name: string;
  score: number;
  metrics?: Record<string, number>;
  output?: Record<string, unknown>;
  validation?: Record<string, unknown>;
}

interface ApiResponse {
  reasoning: ReasoningResult | null;
  validation: ValidationResult | null;
  competition?: CompetitionRow[];
  winner?: string;
  winner_answer?: string;
  reasoning_round_cid?: string;
  knowledge_graph_cid?: string;
  agent_memory_cids?: Record<string, string>;
  agent_memory_registry_cid?: string;
  swarm?: string[];
  error?: string;
}

interface StoryResponse {
  explorerUrl: string;
}

function cidLink(cid: string | undefined): string | null {
  if (!cid || typeof cid !== "string") return null;
  return `${IPFS_GATEWAY}/${cid}`;
}

export default function KairosFrontend(): React.ReactElement {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [query, setQuery] = useState<string>("");
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [result, setResult] = useState<ApiResponse | null>(null);
  const [tab, setTab] = useState<string>("summary");
  const [loading, setLoading] = useState<boolean>(false);
  const [openaiKey, setOpenaiKey] = useState<string>("");
  const [alignmentPreferences, setAlignmentPreferences] = useState<string>("");

  const handleQuery = async (): Promise<void> => {
    setLoading(true);
    try {
      const alignment_profile =
        alignmentPreferences.trim().length > 0
          ? { preferences: alignmentPreferences.trim() }
          : undefined;
      const res = await fetch("/api/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, openai_key: openaiKey, alignment_profile }),
      });
      const raw = await res.text();
      let data: ApiResponse;
      try {
        data = JSON.parse(raw) as ApiResponse;
      } catch {
        setResult({
          error: `Server returned non-JSON (${res.status}): ${raw.slice(0, 500)}`,
          reasoning: null,
          validation: null,
        });
        setTab("summary");
        return;
      }
      if (!res.ok && !data.error) {
        data = { ...data, error: `HTTP ${res.status}` };
      }
      setResult(data);
      if (data.error) {
        setTab("summary");
      }
    } catch (err) {
      console.error("Query failed:", err);
      const msg = err instanceof Error ? err.message : String(err);
      setResult({
        error: `Network or client error: ${msg}. If the dev server is running, check the server terminal for Python stderr.`,
        reasoning: null,
        validation: null,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e: ChangeEvent<HTMLInputElement>): Promise<void> => {
    const file = e.target.files?.[0];
    if (!file) return;
    setPdfFile(file);
    const formData = new FormData();
    formData.append("file", file);
    try {
      await fetch("/api/ingest", { method: "POST", body: formData });
      alert("Upload sent. If your ingest API writes to disk, refresh the knowledge graph for the next run.");
    } catch (err) {
      console.error("Ingestion failed:", err);
    }
  };

  const handleIPRegister = async (): Promise<void> => {
    if (!result?.reasoning) return;

    const ipMetadata = result.reasoning || {};
    const nftMetadata = {
      name: "Kairos Insight",
      description: (result.reasoning?.conclusion as string) || (result.reasoning?.answer as string) || "",
    };
    try {
      const res = await fetch("/api/story/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ip_metadata: ipMetadata, nft_metadata: nftMetadata }),
      });
      const data: StoryResponse = await res.json();
      alert(`IP registered! View: ${data.explorerUrl}`);
    } catch (err) {
      console.error("IP registration failed:", err);
      alert("Failed to register IP. Please try again.");
    }
  };

  const handleLoadSwarmLogs = async (): Promise<void> => {
    try {
      await fetch("/api/swarm");
    } catch (err) {
      console.error("Swarm logs fetch failed:", err);
    }
  };

  const sortedCompetition: CompetitionRow[] = [...(result?.competition ?? [])].sort(
    (a, b) => (b.score ?? 0) - (a.score ?? 0)
  );

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <header className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight">Kairos Reasoning Network</h1>
        <p className="text-muted-foreground text-sm leading-relaxed">
          A <strong className="text-foreground font-medium">marketplace round</strong> runs every reasoning module
          against your knowledge graph, scores each answer with validators, picks a winner, and pins snapshots to IPFS.
        </p>
      </header>

      <Card className="border-muted bg-muted/20">
        <CardContent className="p-5 space-y-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Flow</p>
          <ol className="grid gap-4 sm:grid-cols-3 text-sm">
            <li className="flex gap-3">
              <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/20 text-primary font-semibold text-xs">
                1
              </span>
              <span>
                <span className="font-medium text-foreground flex items-center gap-1.5">
                  <Database className="h-3.5 w-3.5" /> Knowledge graph
                </span>
                <span className="block text-muted-foreground mt-0.5">
                  Ingest documents so entities and relations land in <code className="text-xs bg-black/30 px-1 rounded">output/knowledge_graph.json</code>.
                </span>
              </span>
            </li>
            <li className="flex gap-3">
              <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/20 text-primary font-semibold text-xs">
                2
              </span>
              <span>
                <span className="font-medium text-foreground flex items-center gap-1.5">
                  <GitBranch className="h-3.5 w-3.5" /> Run round
                </span>
                <span className="block text-muted-foreground mt-0.5">
                  All modules answer your question; logical, grounding, and novelty scores produce a leaderboard.
                </span>
              </span>
            </li>
            <li className="flex gap-3">
              <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/20 text-primary font-semibold text-xs">
                3
              </span>
              <span>
                <span className="font-medium text-foreground flex items-center gap-1.5">
                  <Trophy className="h-3.5 w-3.5" /> Winner &amp; CIDs
                </span>
                <span className="block text-muted-foreground mt-0.5">
                  The best-scoring module wins; round and graph payloads are uploaded to IPFS (requires a local IPFS API).
                </span>
              </span>
            </li>
          </ol>
        </CardContent>
      </Card>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">1 · Feed the knowledge graph</h2>
        <Card>
          <CardContent className="p-4 flex flex-col sm:flex-row sm:items-center gap-4 justify-between">
            <div>
              <p className="text-sm text-muted-foreground">
                Upload a PDF to your ingest pipeline (implementation depends on <code className="text-xs">/api/ingest</code>).
                {pdfFile ? (
                  <span className="block mt-1 text-foreground text-sm">Selected: {pdfFile.name}</span>
                ) : null}
              </p>
            </div>
            <input
              ref={fileInputRef}
              type="file"
              accept="application/pdf"
              className="hidden"
              onChange={handleFileUpload}
            />
            <Button type="button" variant="secondary" className="shrink-0" onClick={() => fileInputRef.current?.click()}>
              <Upload className="mr-2 h-4 w-4" /> Upload PDF
            </Button>
          </CardContent>
        </Card>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">2 · Ask and run a marketplace round</h2>
        <Card>
          <CardContent className="p-4 space-y-4">
            <div className="space-y-2">
              <Label htmlFor="query">Question</Label>
              <Textarea
                id="query"
                placeholder="e.g. What are the main risks of this DeFi protocol given the graph?"
                value={query}
                onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setQuery(e.target.value)}
                className="min-h-[100px]"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="openai-override">OpenAI key (optional override)</Label>
              <Input
                id="openai-override"
                type="password"
                autoComplete="off"
                placeholder="Leave empty to use OPENAI_API_KEY from .env on the server"
                value={openaiKey}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setOpenaiKey(e.target.value)}
              />
              <p className="text-xs text-muted-foreground">
                Only needed if you are not using a server-side key. Full scoring uses OpenAI for some modules and validators.
              </p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="alignment-prefs">Alignment preferences (optional)</Label>
              <Textarea
                id="alignment-prefs"
                placeholder="e.g. Prefer conservative, non-speculative language; avoid legal advice."
                value={alignmentPreferences}
                onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setAlignmentPreferences(e.target.value)}
                className="min-h-[72px] text-sm"
              />
              <p className="text-xs text-muted-foreground">
                Passed to the alignment validator alongside logical, grounding, and novelty scores (average of four drives the leaderboard).
              </p>
            </div>
            <Button
              className="w-full sm:w-auto"
              size="lg"
              onClick={handleQuery}
              disabled={loading || !query.trim()}
            >
              <Sparkles className="mr-2 h-4 w-4" />
              {loading ? "Running round…" : "Run marketplace round"}
            </Button>
          </CardContent>
        </Card>
      </section>

      {result ? (
        <section className="space-y-3">
          <div className="flex items-center justify-between gap-2 flex-wrap">
            <h2 className="text-lg font-semibold">3 · Results</h2>
            <Button variant="outline" size="sm" onClick={handleIPRegister} disabled={!result?.reasoning}>
              <Share2 className="mr-2 h-4 w-4" /> Demo: register winner as IP
            </Button>
          </div>

          {result.error ? (
            <Card className="border-destructive/50 bg-destructive/10">
              <CardContent className="p-4 flex gap-3 text-sm">
                <AlertCircle className="h-5 w-5 shrink-0 text-destructive" />
                <div>
                  <p className="font-medium text-destructive">Round failed</p>
                  <p className="text-muted-foreground mt-1 whitespace-pre-wrap">{result.error}</p>
                </div>
              </CardContent>
            </Card>
          ) : null}

          {!result.error && result.winner ? (
            <Card className="border-primary/30 bg-primary/5">
              <CardContent className="p-4 space-y-3">
                <div className="flex items-center gap-2 text-primary font-semibold">
                  <Trophy className="h-5 w-5" /> Winning module: {result.winner}
                </div>
                <div>
                  <p className="text-xs uppercase text-muted-foreground mb-1">Answer</p>
                  <p className="text-sm whitespace-pre-wrap leading-relaxed">
                    {result.winner_answer || result.reasoning?.answer || result.reasoning?.conclusion || "—"}
                  </p>
                </div>
                <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3 text-xs">
                  <div>
                    <span className="text-muted-foreground">Knowledge graph CID</span>
                    {result.knowledge_graph_cid ? (
                      <a
                        href={cidLink(result.knowledge_graph_cid) ?? "#"}
                        target="_blank"
                        rel="noreferrer"
                        className="flex items-center gap-1 text-primary hover:underline break-all"
                      >
                        {result.knowledge_graph_cid}
                        <ExternalLink className="h-3 w-3 shrink-0" />
                      </a>
                    ) : (
                      <span className="block text-muted-foreground">—</span>
                    )}
                  </div>
                  <div>
                    <span className="text-muted-foreground">Reasoning round CID</span>
                    {result.reasoning_round_cid ? (
                      <a
                        href={cidLink(result.reasoning_round_cid) ?? "#"}
                        target="_blank"
                        rel="noreferrer"
                        className="flex items-center gap-1 text-primary hover:underline break-all"
                      >
                        {result.reasoning_round_cid}
                        <ExternalLink className="h-3 w-3 shrink-0" />
                      </a>
                    ) : (
                      <span className="block text-muted-foreground">—</span>
                    )}
                  </div>
                  <div className="sm:col-span-2 lg:col-span-1">
                    <span className="text-muted-foreground">Agent registry checkpoint CID</span>
                    {result.agent_memory_registry_cid ? (
                      <a
                        href={cidLink(result.agent_memory_registry_cid) ?? "#"}
                        target="_blank"
                        rel="noreferrer"
                        className="flex items-center gap-1 text-primary hover:underline break-all"
                      >
                        {result.agent_memory_registry_cid}
                        <ExternalLink className="h-3 w-3 shrink-0" />
                      </a>
                    ) : (
                      <span className="block text-muted-foreground">—</span>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ) : null}

          <Tabs value={tab} onValueChange={setTab} className="w-full">
            <TabsList className="flex flex-wrap h-auto gap-1">
              <TabsTrigger value="summary">Summary</TabsTrigger>
              <TabsTrigger value="leaderboard">Leaderboard</TabsTrigger>
              <TabsTrigger value="validation">
                <Shield className="h-3.5 w-3.5 mr-1 inline" /> Winner validation
              </TabsTrigger>
              <TabsTrigger value="graph">Graph viz</TabsTrigger>
              <TabsTrigger value="swarm">Swarm</TabsTrigger>
            </TabsList>

            <TabsContent value="summary" className="mt-3">
              <Card>
                <CardContent className="p-4 space-y-3 text-sm">
                  <p className="text-muted-foreground text-xs">
                    Raw payload for debugging (winner, CIDs, full reasoning object).
                  </p>
                  <pre className="whitespace-pre-wrap break-words text-xs bg-black/25 p-3 rounded-md overflow-x-auto">
                    {JSON.stringify(
                      {
                        winner: result?.winner,
                        winner_answer: result?.winner_answer,
                        reasoning_round_cid: result?.reasoning_round_cid,
                        knowledge_graph_cid: result?.knowledge_graph_cid,
                        agent_memory_cids: result?.agent_memory_cids,
                        agent_memory_registry_cid: result?.agent_memory_registry_cid,
                        reasoning: result?.reasoning,
                      },
                      null,
                      2
                    )}
                  </pre>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="leaderboard" className="mt-3">
              <Card>
                <CardContent className="p-0 overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-border text-left text-xs text-muted-foreground">
                        <th className="p-3 font-medium">#</th>
                        <th className="p-3 font-medium">Module</th>
                        <th className="p-3 font-medium">Score</th>
                        <th className="p-3 font-medium hidden sm:table-cell">Logical</th>
                        <th className="p-3 font-medium hidden sm:table-cell">Grounding</th>
                        <th className="p-3 font-medium hidden md:table-cell">Novelty</th>
                        <th className="p-3 font-medium hidden md:table-cell">Align</th>
                      </tr>
                    </thead>
                    <tbody>
                      {sortedCompetition.length === 0 ? (
                        <tr>
                          <td colSpan={8} className="p-4 text-muted-foreground text-center">
                            No competition data — run a round after fixing errors.
                          </td>
                        </tr>
                      ) : (
                        sortedCompetition.map((row, i) => (
                          <tr
                            key={row.module_name}
                            className={
                              row.module_name === result?.winner
                                ? "bg-primary/10 border-l-2 border-l-primary"
                                : "border-b border-border/50"
                            }
                          >
                            <td className="p-3 text-muted-foreground">{i + 1}</td>
                            <td className="p-3 font-medium">{row.module_name}</td>
                            <td className="p-3 tabular-nums">{row.score?.toFixed?.(4) ?? row.score}</td>
                            <td className="p-3 tabular-nums hidden sm:table-cell">
                              {row.metrics?.logical_consistency?.toFixed?.(2) ?? "—"}
                            </td>
                            <td className="p-3 tabular-nums hidden sm:table-cell">
                              {row.metrics?.grounding?.toFixed?.(2) ?? "—"}
                            </td>
                            <td className="p-3 tabular-nums hidden md:table-cell">
                              {row.metrics?.novelty?.toFixed?.(2) ?? "—"}
                            </td>
                            <td className="p-3 tabular-nums hidden md:table-cell">
                              {row.metrics?.alignment?.toFixed?.(2) ?? "—"}
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="validation" className="mt-3">
              <Card>
                <CardContent className="p-4">
                  <p className="text-xs text-muted-foreground mb-2">Validators for the winning module only.</p>
                  <pre className="whitespace-pre-wrap break-words text-xs bg-black/25 p-3 rounded-md overflow-x-auto">
                    {JSON.stringify(result?.validation, null, 2)}
                  </pre>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="graph" className="mt-3">
              <Card>
                <CardContent className="p-4 text-sm text-muted-foreground">
                  <p>
                    Interactive graph visualization is not implemented yet. The knowledge graph is serialized and pinned
                    as JSON; use the <strong className="text-foreground">Knowledge graph CID</strong> above to inspect the
                    snapshot on an IPFS gateway.
                  </p>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="swarm" className="mt-3">
              <Card>
                <CardContent className="p-4 space-y-2 text-sm text-muted-foreground">
                  <p>Optional demo hook for swarm-style stats (not part of the core marketplace flow).</p>
                  <Button variant="secondary" size="sm" onClick={handleLoadSwarmLogs}>
                    Load Swarm Logs
                  </Button>
                  <pre className="text-xs whitespace-pre-wrap bg-black/25 p-2 rounded mt-2">
                    {result?.swarm?.join("\n") ?? "No swarm data loaded."}
                  </pre>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </section>
      ) : (
        <p className="text-sm text-muted-foreground text-center py-6 border border-dashed rounded-lg">
          Run a marketplace round to see scores, CIDs, and validation here.
        </p>
      )}
    </div>
  );
}
