import datetime

from reasoning_modules.base.module import ReasoningModule
from reasoning_modules.kg_triple_strings import module_scoped_triples
from reasoning_modules.memory_hints import memory_learning_hint


class AuditReasoningModule(ReasoningModule):
    def __init__(self):
        super().__init__('audit')
        self.sources = {
            "audit_history": "Smart Contract Audit Database",
            "vulnerability_tracker": "DeFi Exploit Monitor",
            "security_practices": "Protocol Security Standards"
        }

    def run(self, subquery, knowledgeGraph, memory_context=None):
        audit_facts = knowledgeGraph.query(subject="TokenX", subject_type="SmartContract")
        vulnerability_data = knowledgeGraph.query(predicate="has_vulnerability")
        memory_context = memory_context or {}
        previous_scores = memory_context.get("performance_history", [])
        if not isinstance(previous_scores, list):
            previous_scores = []
        numeric_scores = [float(s) for s in previous_scores if isinstance(s, (int, float))]
        avg_score = sum(numeric_scores) / len(numeric_scores) if numeric_scores else 0.0
        learning_hint = memory_learning_hint(numeric_scores)

        reasoning_steps = [
            {
                "step": "Review audit history",
                "data": "Smart contract has not been audited in 2 years",
                "source": self.sources["audit_history"],
                "inference": "Outdated security verification"
            },
            {
                "step": "Analyze similar contracts",
                "data": "Recent similar contracts have been exploited",
                "source": self.sources["vulnerability_tracker"],
                "inference": "Pattern of vulnerabilities in similar implementations"
            },
            {
                "step": "Evaluate security practices",
                "data": "No bug bounty program in place",
                "source": self.sources["security_practices"],
                "inference": "Limited incentives for vulnerability disclosure"
            }
        ]
        
        conclusion = "Smart contract audit status indicates high risk"
        if numeric_scores and sum(1 for s in numeric_scores[-5:] if s < 0.35) >= 2:
            conclusion += " (elevated caution: recent validator scores for this agent were weak—double-check assumptions)."

        source_triples = module_scoped_triples(
            knowledgeGraph,
            "audit",
            [
                {"subject": "TokenX", "subject_type": "SmartContract"},
                {"predicate": "has_vulnerability"},
            ],
        )

        return {
            "subquery": subquery,
            "timestamp": datetime.datetime.now().isoformat(),
            "reasoningPath": reasoning_steps,
            "sources": self.sources,
            "conclusion": conclusion,
            "confidence": 0.78,
            "relevantMetrics": {
                "last_audit_age": "24 months",
                "similar_exploits": "3 in last 6 months",
                "security_score": "low",
                "memory_avg_score": round(avg_score, 4),
                "memory_learning_hint": learning_hint,
            },
            "memory_context_used": {
                "past_round_count": len(memory_context.get("past_round_cids", [])),
                "recent_performance_points": len(numeric_scores),
            },
            "source_triples": source_triples,
        }