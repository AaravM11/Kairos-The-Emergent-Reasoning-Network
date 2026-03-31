"""Build `source_triples` strings for grounding_vn from KnowledgeGraph queries."""

import hashlib
from typing import Any, Dict, List


def triple_strings_from_queries(knowledge_graph: Any, query_specs: List[Dict[str, Any]], limit: int = 12) -> List[str]:
    """
    Run each kg.query(**spec) and format edges as 'Subject --predicate--> Object'.
    Dedupes and caps list length.
    """
    seen: set = set()
    out: List[str] = []
    for spec in query_specs:
        for subj, rel, obj in knowledge_graph.query(**spec):
            line = f"{subj.label} --{rel.predicate}--> {obj.label}"
            if line in seen:
                continue
            seen.add(line)
            out.append(line)
            if len(out) >= limit:
                return out
    return out


def fallback_triples_from_graph(knowledge_graph: Any, limit: int = 12) -> List[str]:
    """All relations in the KG (when targeted queries return nothing)."""
    return triple_strings_from_queries(knowledge_graph, [{}], limit=limit)


def module_scoped_triples(
    knowledge_graph: Any,
    module_name: str,
    query_specs: List[Dict[str, Any]],
    limit: int = 12,
) -> List[str]:
    """
    Primary triples from module-specific queries, then fill from a rotation of all KG edges
    keyed by module_name so agents claim different order/subsets when the graph is small.
    """
    primary = triple_strings_from_queries(knowledge_graph, query_specs, limit=limit)
    all_lines: List[str] = []
    for subj, rel, obj in knowledge_graph.query():
        all_lines.append(f"{subj.label} --{rel.predicate}--> {obj.label}")
    uniq = sorted(set(all_lines))
    if not uniq:
        return primary[:limit]
    h = int(hashlib.md5(module_name.encode("utf-8"), usedforsecurity=False).hexdigest(), 16) % len(uniq)
    rotated = uniq[h:] + uniq[:h]
    out: List[str] = []
    seen: set = set()
    for t in primary + rotated:
        if t in seen:
            continue
        seen.add(t)
        out.append(t)
        if len(out) >= limit:
            break
    return out
