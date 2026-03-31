import React, { useState, ChangeEvent } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@radix-ui/react-label";
import { Upload, Sparkles, Share2 } from "lucide-react";

// Define types
interface ReasoningResult {
  conclusion?: string;
  [key: string]: any;
}

interface ValidationResult {
  [key: string]: any;
}

interface ApiResponse {
  reasoning: ReasoningResult | null;
  validation: ValidationResult | null;
  competition?: Array<{
    module_name: string;
    score: number;
    metrics: Record<string, number>;
    output: Record<string, any>;
  }>;
  winner?: string;
  winner_answer?: string;
  reasoning_round_cid?: string;
  knowledge_graph_cid?: string;
  agent_memory_cids?: Record<string, string>;
  swarm?: string[];
  error?: string;
}

interface StoryResponse {
  explorerUrl: string;
}

export default function KairosFrontend() {
  const [query, setQuery] = useState<string>("");
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [result, setResult] = useState<ApiResponse | null>(null);
  const [tab, setTab] = useState<string>("reasoning");
  const [loading, setLoading] = useState<boolean>(false);
  const [openaiKey, setOpenaiKey] = useState<string>("");

  const handleQuery = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, openai_key: openaiKey }),
      });
      const data: ApiResponse = await res.json();
      setResult(data);
    } catch (err) {
      console.error("Query failed:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setPdfFile(file);
    const formData = new FormData();
    formData.append("file", file);
    try {
      await fetch("/api/ingest", { method: "POST", body: formData });
      alert("PDF ingested successfully.");
    } catch (err) {
      console.error("Ingestion failed:", err);
    }
  };

  const handleIPRegister = async () => {
    if (!result?.reasoning) return;

    const ipMetadata = result.reasoning || {};
    const nftMetadata = {
      name: "Kairos Insight",
      description: result.reasoning?.conclusion || "",
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

  const handleLoadSwarmLogs = async () => {
    try {
      const res = await fetch("/api/swarm");
      const data = await res.json();
      // setResult((prev) => ({
        // ...prev,
        // swarm: data.lines || ["No logs found"],
      // }));
    } catch (err) {
      console.error("Swarm logs fetch failed:", err);
    }
  };

  return (
    <div className="p-8 space-y-8">
      <h1 className="text-3xl font-bold tracking-tight">Kairos Reasoning Network</h1>
      <Card className="p-4 space-y-4">
        <Label htmlFor="query">Query</Label>
        <Textarea
          id="query"
          placeholder="What are the risks of this DeFi protocol?"
          value={query}
          onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setQuery(e.target.value)}
        />
        <div className="flex gap-4">
          <Input
            placeholder="OpenAI key (required for full scoring)"
            value={openaiKey}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setOpenaiKey(e.target.value)}
          />
          <Button onClick={handleQuery} disabled={loading}>
            <Sparkles className="mr-2 h-4 w-4" /> Generate
          </Button>
          <Label className="flex items-center gap-2 cursor-pointer">
            <Upload className="h-4 w-4" /> Upload PDF
            <Input type="file" accept="application/pdf" className="hidden" onChange={handleFileUpload} />
          </Label>
          <Button variant="secondary" onClick={handleIPRegister} disabled={!result}>
            <Share2 className="mr-2 h-4 w-4" /> Register as IP
          </Button>
        </div>
      </Card>

      <Tabs value={tab} onValueChange={setTab} className="w-full">
        <TabsList>
          <TabsTrigger value="reasoning">Reasoning</TabsTrigger>
          <TabsTrigger value="competition">Competition</TabsTrigger>
          <TabsTrigger value="validation">Validation</TabsTrigger>
          <TabsTrigger value="graph">Reasoning Pathway</TabsTrigger>
          <TabsTrigger value="swarm">Swarm Stats</TabsTrigger>
        </TabsList>

        <TabsContent value="reasoning">
          <Card>
            <CardContent className="p-4 whitespace-pre-wrap text-sm">
              {JSON.stringify(
                {
                  winner: result?.winner,
                  winner_answer: result?.winner_answer,
                  reasoning_round_cid: result?.reasoning_round_cid,
                  knowledge_graph_cid: result?.knowledge_graph_cid,
                  reasoning: result?.reasoning,
                },
                null,
                2
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="competition">
          <Card>
            <CardContent className="p-4 whitespace-pre-wrap text-sm">
              {JSON.stringify(result?.competition, null, 2)}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="validation">
          <Card><CardContent className="p-4 whitespace-pre-wrap text-sm">{JSON.stringify(result?.validation, null, 2)}</CardContent></Card>
        </TabsContent>

        <TabsContent value="graph">
          <Card><CardContent className="p-4"><i>Reasoning graph visualization coming soon...</i></CardContent></Card>
        </TabsContent>

        <TabsContent value="swarm">
          <Card>
            <CardContent className="p-4 space-y-2">
              <Button onClick={handleLoadSwarmLogs}>
                Load Swarm Logs
              </Button>
              <pre className="text-sm whitespace-pre-wrap bg-gray-800 p-2 rounded">
                {result?.swarm?.join("\n") ?? "No swarm data loaded."}
              </pre>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
