import importlib
import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from core.llm_client import llm_ready
from core.storage.ipfs import upload_to_ipfs, fetch_json_from_ipfs, persist_cid_to_filecoin


RM_REGISTRY = {
    "defi_risk": {
        "module": "reasoning_modules.defi_risk.index",
        "class": "DeFiRiskReasoningModule",
        "requires_openai": True,
    },
    "audit": {
        "module": "reasoning_modules.audit_rm",
        "class": "AuditReasoningModule",
        "requires_openai": False,
    },
    "macro": {
        "module": "reasoning_modules.macro_rm",
        "class": "MacroReasoningModule",
        "requires_openai": False,
    },
    "sentiment": {
        "module": "reasoning_modules.sentiment_rm",
        "class": "SentimentReasoningModule",
        "requires_openai": False,
    },
}

VN_REGISTRY = {
    "logical": {
        "module": "validation_nodes.logical_vn",
        "function": "run_logical_vn",
        "requires_openai": True,
        "requires_kg": False,
    },
    "grounding": {
        "module": "validation_nodes.grounding_vn",
        "function": "run_grounding_vn",
        "requires_openai": False,
        "requires_kg": True,
    },
    "novelty": {
        "module": "validation_nodes.novelty_vn",
        "function": "run_novelty_vn",
        "requires_openai": True,
        "requires_kg": True,
    },
    "alignment": {
        "module": "validation_nodes.alignment_vn",
        "function": "run_alignment_vn_from_dict",
        "requires_openai": True,
        "requires_kg": False,
    },
}


@dataclass
class AgentMemory:
    agent_name: str
    past_round_cids: List[str] = field(default_factory=list)
    performance_history: List[float] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "past_round_cids": self.past_round_cids,
            "performance_history": self.performance_history,
            "metadata": self.metadata,
        }


@dataclass
class ReasoningRound:
    query: str
    timestamp: str
    knowledge_graph_cid: str
    results: List[Dict[str, Any]]
    winner: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "timestamp": self.timestamp,
            "knowledge_graph_cid": self.knowledge_graph_cid,
            "results": self.results,
            "winner": self.winner,
            "metadata": self.metadata,
        }


MEMORY_REGISTRY_PATH = os.environ.get(
    "AGENT_MEMORY_REGISTRY_PATH", "output/agent_memory_registry.json"
)


def _ensure_output_dir() -> None:
    output_dir = os.path.dirname(MEMORY_REGISTRY_PATH) or "output"
    os.makedirs(output_dir, exist_ok=True)


def _load_memory_registry() -> Dict[str, str]:
    _ensure_output_dir()
    if not os.path.exists(MEMORY_REGISTRY_PATH):
        return {}
    with open(MEMORY_REGISTRY_PATH, "r", encoding="utf-8") as fp:
        return json.load(fp)


def _save_memory_registry(registry: Dict[str, str]) -> None:
    _ensure_output_dir()
    with open(MEMORY_REGISTRY_PATH, "w", encoding="utf-8") as fp:
        json.dump(registry, fp, indent=2)


def _serialize_knowledge_graph(knowledge_graph: Any) -> Dict[str, Any]:
    return {
        "entities": [entity.to_dict() for entity in knowledge_graph.entities.values()],
        "relations": [relation.to_dict() for relation in knowledge_graph.relations],
    }


def _normalize_rm_output(module_name: str, output: Dict[str, Any]) -> Dict[str, Any]:
    conclusion = output.get("conclusion") or output.get("answer") or ""
    steps = output.get("reasoning_steps")
    if not steps and "reasoningPath" in output:
        steps = []
        for step in output["reasoningPath"]:
            if isinstance(step, dict):
                steps.append(step.get("data") or step.get("inference") or str(step))
            else:
                steps.append(str(step))

    normalized = dict(output)
    normalized["module_used"] = module_name
    normalized["answer"] = conclusion
    normalized["reasoning_steps"] = steps or []
    normalized["source_triples"] = output.get("source_triples", [])
    return normalized


def _run_module(
    module_name: str,
    rm_info: Dict[str, Any],
    query: str,
    knowledge_graph: Any,
    openai_key: Optional[str],
    memory_context: Dict[str, Any],
) -> Dict[str, Any]:
    rm_module = importlib.import_module(rm_info["module"])
    rm_class = getattr(rm_module, rm_info["class"])
    instance = rm_class()
    if rm_info.get("requires_openai", False):
        output = instance.run(
            query, knowledge_graph, openai_key=openai_key, memory_context=memory_context
        )
    else:
        output = instance.run(query, knowledge_graph, memory_context=memory_context)
    return _normalize_rm_output(module_name, output)


def _run_validations_for_output(
    output: Dict[str, Any],
    knowledge_graph: Any,
    openai_key: Optional[str],
    alignment_profile: Optional[Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    metrics: Dict[str, Dict[str, Any]] = {}
    for vn_name, vn_info in VN_REGISTRY.items():
        if vn_info.get("requires_openai") and not llm_ready(openai_key):
            metrics[vn_name] = {
                "vn_type": vn_name,
                "valid": False,
                "score": 0.0,
                "feedback": "Skipped: set OPENAI_API_KEY or LLM_PROVIDER=ollama with Ollama running.",
            }
            continue
        try:
            vn_module = importlib.import_module(vn_info["module"])
            vn_function = getattr(vn_module, vn_info["function"])
            if vn_name == "alignment":
                metrics[vn_name] = vn_function(output, openai_key, alignment_profile)
            else:
                args = [output]
                if vn_info.get("requires_kg"):
                    args.append(knowledge_graph)
                if vn_info.get("requires_openai"):
                    args.append(openai_key)
                metrics[vn_name] = vn_function(*args)
        except Exception as exc:
            metrics[vn_name] = {
                "vn_type": vn_name,
                "valid": False,
                "score": 0.0,
                "feedback": f"Validation error: {exc}",
            }
    return metrics


def validate_all(
    results: List[Dict[str, Any]],
    knowledge_graph: Any,
    openai_key: Optional[str],
    alignment_profile: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    scored: List[Dict[str, Any]] = []
    for item in results:
        output = item["output"]
        validation_metrics = _run_validations_for_output(
            output, knowledge_graph, openai_key, alignment_profile
        )
        metric_scores = {
            "logical_consistency": validation_metrics.get("logical", {}).get("score", 0.0),
            "grounding": validation_metrics.get("grounding", {}).get("score", 0.0),
            "novelty": validation_metrics.get("novelty", {}).get("score", 0.0),
            "alignment": validation_metrics.get("alignment", {}).get("score", 0.0),
        }
        validator_avg = (
            metric_scores["logical_consistency"]
            + metric_scores["grounding"]
            + metric_scores["novelty"]
            + metric_scores["alignment"]
        ) / 4.0
        raw_conf = output.get("confidence", 0.5)
        try:
            module_confidence = float(raw_conf)
        except (TypeError, ValueError):
            module_confidence = 0.5
        module_confidence = max(0.0, min(1.0, module_confidence))
        metric_scores["validator_average"] = round(validator_avg, 4)
        metric_scores["module_confidence"] = round(module_confidence, 4)
        # Blend so leaderboard differentiates when validators tie (e.g. LLM parse failures).
        final_score = round(validator_avg * 0.72 + module_confidence * 0.28, 4)
        scored.append(
            {
                "module_name": item["module_name"],
                "output": output,
                "score": final_score,
                "metrics": metric_scores,
                "validation": validation_metrics,
            }
        )
    return scored


def _load_memory_for_agent(agent_name: str, registry: Dict[str, str]) -> Tuple[AgentMemory, Optional[str]]:
    last_cid = registry.get(agent_name)
    if not last_cid:
        return AgentMemory(agent_name=agent_name), None
    try:
        memory_payload = fetch_json_from_ipfs(last_cid)
    except Exception:
        # Stale CID, gateway unreachable, or fake-IPFS mode without this blob — start fresh for this agent.
        return AgentMemory(agent_name=agent_name), None
    return (
        AgentMemory(
            agent_name=memory_payload.get("agent_name", agent_name),
            past_round_cids=memory_payload.get("past_round_cids", []),
            performance_history=memory_payload.get("performance_history", []),
            metadata=memory_payload.get("metadata", {}),
        ),
        last_cid,
    )


def orchestrate(
    query: str,
    knowledge_graph: Any,
    openai_key: Optional[str] = None,
    run_validation: bool = True,
    alignment_profile: Optional[Dict] = None,
) -> Dict[str, Any]:
    try:
        kg_cid = upload_to_ipfs(_serialize_knowledge_graph(knowledge_graph))
        memory_registry = _load_memory_registry()

        module_results: List[Dict[str, Any]] = []
        loaded_memory_cids: Dict[str, Optional[str]] = {}
        for module_name, rm_info in RM_REGISTRY.items():
            if rm_info.get("requires_openai", False) and not llm_ready(openai_key):
                continue
            agent_memory, memory_cid = _load_memory_for_agent(module_name, memory_registry)
            loaded_memory_cids[module_name] = memory_cid
            memory_context = {
                "past_round_cids": agent_memory.past_round_cids[-5:],
                "performance_history": agent_memory.performance_history[-20:],
                "metadata": agent_memory.metadata,
            }
            output = _run_module(
                module_name, rm_info, query, knowledge_graph, openai_key, memory_context
            )
            module_results.append({"module_name": module_name, "output": output})

        if not module_results:
            raise ValueError("No reasoning modules available to run")

        scored_results = (
            validate_all(module_results, knowledge_graph, openai_key, alignment_profile)
            if run_validation
            else [
                {
                    "module_name": item["module_name"],
                    "output": item["output"],
                    "score": float(item["output"].get("confidence", 0.0)),
                    "metrics": {},
                    "validation": {},
                }
                for item in module_results
            ]
        )
        winner_entry = max(scored_results, key=lambda x: x["score"])
        winner = winner_entry["module_name"]

        round_obj = ReasoningRound(
            query=query,
            timestamp=datetime.now(timezone.utc).isoformat(),
            knowledge_graph_cid=kg_cid,
            results=scored_results,
            winner=winner,
            metadata={
                "alignment_profile": alignment_profile or {},
                "memory_registry_before_round": loaded_memory_cids,
            },
        )
        round_payload = round_obj.to_dict()
        round_cid = upload_to_ipfs(round_payload)
        round_filecoin = persist_cid_to_filecoin(round_cid)

        updated_memory_cids: Dict[str, str] = {}
        for item in scored_results:
            agent_name = item["module_name"]
            existing_memory, _ = _load_memory_for_agent(agent_name, memory_registry)
            existing_memory.past_round_cids.append(round_cid)
            existing_memory.performance_history.append(item["score"])
            existing_memory.metadata["last_score"] = item["score"]
            existing_memory.metadata["last_updated"] = datetime.now(timezone.utc).isoformat()
            memory_cid = upload_to_ipfs(existing_memory.to_dict())
            memory_registry[agent_name] = memory_cid
            updated_memory_cids[agent_name] = memory_cid
        _save_memory_registry(memory_registry)

        registry_checkpoint_cid: Optional[str] = None
        try:
            with open(MEMORY_REGISTRY_PATH, "r", encoding="utf-8") as reg_fp:
                registry_snapshot = json.load(reg_fp)
            registry_checkpoint_cid = upload_to_ipfs(
                {
                    "type": "agent_memory_registry_checkpoint",
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "agents": registry_snapshot,
                    "last_reasoning_round_cid": round_cid,
                }
            )
        except OSError:
            pass

        try:
            from core.storage.round_archive import append_marketplace_round

            append_marketplace_round(
                {
                    "archived_at": datetime.now(timezone.utc).isoformat(),
                    "query": query,
                    "winner": winner,
                    "winner_answer": winner_entry["output"].get("answer", ""),
                    "knowledge_graph_cid": kg_cid,
                    "reasoning_round_cid": round_cid,
                    "agent_memory_registry_cid": registry_checkpoint_cid,
                    "reasoning_round_filecoin": round_filecoin,
                }
            )
        except Exception:
            pass

        return {
            "reasoning": winner_entry["output"],
            "validation": winner_entry["validation"],
            "competition": scored_results,
            "winner": winner,
            "winner_answer": winner_entry["output"].get("answer", ""),
            "knowledge_graph_cid": kg_cid,
            "reasoning_round_cid": round_cid,
            "reasoning_round_filecoin": round_filecoin,
            "agent_memory_cids": updated_memory_cids,
            "agent_memory_registry_cid": registry_checkpoint_cid,
            "round": round_payload,
        }
    except Exception as exc:
        return {
            "error": str(exc),
            "reasoning": None,
            "validation": {},
            "competition": [],
        }