import openai
import datetime
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from core.openai_model import default_chat_model
from reasoning_modules.base.module import ReasoningModule
from reasoning_modules.memory_hints import memory_learning_hint


class DeFiRiskReasoningModule(ReasoningModule):
    def __init__(self):
        super().__init__('defi-risk')
        self.sources = {
            "protocol_data": "DeFi Protocol Database",
            "market_data": "Crypto Market Analytics",
            "security_data": "Smart Contract Security Monitor"
        }

    def run(self, subquery, knowledgeGraph, openai_key=None, memory_context=None):
        if not openai_key:
            raise ValueError("OpenAI API key is required for DeFi risk analysis")
        memory_context = memory_context or {}
        past_scores = memory_context.get("performance_history", [])
        if not isinstance(past_scores, list):
            past_scores = []
        numeric_scores = [float(s) for s in past_scores if isinstance(s, (int, float))]
        memory_hint = (
            f"Past performance average: {round(sum(numeric_scores) / len(numeric_scores), 4)}"
            if numeric_scores
            else "No historical performance yet"
        )
        learning_hint = memory_learning_hint(numeric_scores)

        openai.api_key = openai_key

        # Extract relevant triples from the KG
        relevant_triples = knowledgeGraph.query(subject=None, predicate=None, object_=None)
        triples_text = "\n".join(
            f"{s.label} --{r.predicate}--> {o.label}" for s, r, o in relevant_triples
        )

        # Ask GPT to reason over the facts and answer the query
        prompt = f"""
You are a DeFi risk analysis agent. You are given the following structured facts:

{triples_text}

User query: "{subquery}"

Historical memory context:
{memory_hint}

Learning guidance from prior marketplace scores:
{learning_hint}

Based on the facts above, provide:
1. A short answer to the query
2. A step-by-step reasoning process leading to the answer
3. Which of the above facts support your reasoning

Respond in this exact format:

Answer: <short-answer>
Reasoning:
- Step 1: ...
- Step 2: ...
Sources:
- <subject> --<predicate>--> <object>
"""

        response = openai.ChatCompletion.create(
            model=default_chat_model(),
            messages=[{"role": "user", "content": prompt}],
        )

        content = response["choices"][0]["message"]["content"]

        # Parse output
        try:
            answer = content.split("Answer:")[1].split("Reasoning:")[0].strip()
            reasoning_lines = content.split("Reasoning:")[1].split("Sources:")[0].strip().split("\n")
            reasoning_steps = [line.strip("- ").strip() for line in reasoning_lines if line.strip()]
            source_lines = content.split("Sources:")[1].strip().split("\n")
            source_triples = [line.strip("- ").strip() for line in source_lines if line.strip()]
            
            # Convert reasoning steps to structured format
            structured_steps = []
            for i, step in enumerate(reasoning_steps):
                structured_steps.append({
                    "step": f"Step {i+1}",
                    "data": step,
                    "source": self.sources.get("protocol_data", "Analysis"),
                    "inference": step
                })
            
            # Calculate confidence based on number of sources
            confidence = min(0.95, 0.5 + (len(source_triples) * 0.1))
            
            return {
                "subquery": subquery,
                "timestamp": datetime.datetime.now().isoformat(),
                "reasoningPath": structured_steps,
                "sources": self.sources,
                "conclusion": answer,
                "confidence": confidence,
                "source_triples": source_triples,
                "relevantMetrics": {
                    "source_count": len(source_triples),
                    "reasoning_steps": len(reasoning_steps)
                },
                "memory_context_used": {
                    "past_round_count": len(memory_context.get("past_round_cids", [])),
                    "recent_performance_points": len(past_scores),
                },
            }
            
        except Exception as e:
            print(f"Failed to parse RM output: {e}")
            return {
                "subquery": subquery,
                "timestamp": datetime.datetime.now().isoformat(),
                "reasoningPath": [],
                "sources": self.sources,
                "conclusion": "Could not parse response.",
                "confidence": 0.0,
                "source_triples": [],
                "relevantMetrics": {}
            }


# For backward compatibility
def run_defi_risk_rm(query, kg, openai_key):
    """Legacy function for backward compatibility"""
    rm = DeFiRiskReasoningModule()
    result = rm.run(query, kg, openai_key)
    
    # Convert to old format for compatibility
    return {
        "module": "defi-risk",
        "answer": result["conclusion"],
        "reasoning_steps": [step["data"] for step in result["reasoningPath"]],
        "source_triples": result["source_triples"],
        "confidence": result["confidence"]
    }
