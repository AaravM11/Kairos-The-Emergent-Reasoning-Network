#!/usr/bin/env python3
import argparse
import os
import sys
import json

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.knowledge_graph.knowledgeGraph import KnowledgeGraph
from core.orchestrator.index import orchestrate

def main():
    parser = argparse.ArgumentParser(description="Kairos Emergent Reasoning Network CLI")
    parser.add_argument("--query", "-q", required=True, help="Query to process")
    parser.add_argument("--kg-path", default="output/knowledge_graph.json", 
                        help="Path to knowledge graph JSON file")
    parser.add_argument("--openai-key", help="OpenAI API key (or set OPENAI_API_KEY env var)")
    parser.add_argument("--no-validation", action="store_true", 
                        help="Skip validation nodes")
    parser.add_argument("--output", "-o", help="Output file for results (JSON)")
    
    args = parser.parse_args()
    
    # Get OpenAI key from args or environment
    openai_key = args.openai_key or os.environ.get("OPENAI_API_KEY")
    if not openai_key:
        print("Warning: No OpenAI API key provided. Some features may not work.")
    
    # Load knowledge graph
    print(f"Loading knowledge graph from {args.kg_path}...")
    kg = KnowledgeGraph()
    kg.load_from_json(args.kg_path)
    
    # Process query
    print(f"Processing query: {args.query}")
    result = orchestrate(
        query=args.query,
        knowledge_graph=kg,
        openai_key=openai_key,
        run_validation=not args.no_validation
    )
    
    if result.get("error"):
        print(f"\nError: {result['error']}")
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)
            print(f"Partial/error result saved to {args.output}")
        return

    # Display results
    print("\n=== Marketplace round ===")
    print(f"Winner: {result.get('winner', '?')}")
    reasoning = result.get("reasoning") or {}
    ans = reasoning.get("answer") or reasoning.get("conclusion") or "—"
    print(f"Winner answer: {ans}")
    print(f"Knowledge graph CID: {result.get('knowledge_graph_cid', '—')}")
    print(f"Reasoning round CID: {result.get('reasoning_round_cid', '—')}")
    print(f"Registry checkpoint CID: {result.get('agent_memory_registry_cid', '—')}")

    print("\n=== Leaderboard ===")
    for row in result.get("competition", []):
        m = row.get("metrics") or {}
        print(
            f"  {row.get('module_name')}: score={row.get('score')} "
            f"(L={m.get('logical_consistency')} G={m.get('grounding')} "
            f"N={m.get('novelty')} A={m.get('alignment')})"
        )

    print("\n=== Winner reasoning (excerpt) ===")
    print(f"Module: {reasoning.get('module_used', 'unknown')}")
    for step in reasoning.get("reasoning_steps", [])[:5]:
        if isinstance(step, dict):
            print(f"- {step.get('step', 'Step')}: {step.get('data', '')}")
        else:
            print(f"- {step}")

    if result.get("validation"):
        print("\n=== Validation (winner) ===")
        for vn_name, vn_result in result["validation"].items():
            valid = vn_result.get("valid", False)
            score = vn_result.get("score", 0.0)
            status = "pass" if valid else "fail"
            print(f"{vn_name}: {status} (score {score}) — {vn_result.get('feedback', '')[:120]}")
    
    # Save to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\nResults saved to {args.output}")

if __name__ == "__main__":
    main()