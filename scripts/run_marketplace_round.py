#!/usr/bin/env python3
import json
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.knowledge_graph.knowledgeGraph import KnowledgeGraph
from core.orchestrator.index import orchestrate


def main() -> None:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
        query = payload.get("query")
        if not query:
            raise ValueError("query is required")

        kg_path = payload.get("kg_path", "output/knowledge_graph.json")
        openai_key = payload.get("openai_key") or os.environ.get("OPENAI_API_KEY")
        run_validation = payload.get("run_validation", True)

        kg = KnowledgeGraph()
        kg.load_from_json(kg_path)

        result = orchestrate(
            query=query,
            knowledge_graph=kg,
            openai_key=openai_key,
            run_validation=run_validation,
            alignment_profile=payload.get("alignment_profile"),
        )
        print(json.dumps(result))
    except Exception as exc:
        print(json.dumps({"error": str(exc)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
