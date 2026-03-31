from reasoning_modules.base.module import ReasoningModule
import datetime

class MacroReasoningModule(ReasoningModule):
    def __init__(self):
        super().__init__('macro')
        self.sources = {
            "fed_data": "Federal Reserve Economic Data",
            "market_indices": "Major Market Indices",
            "inflation_reports": "Bureau of Labor Statistics"
        }

    def run(self, subquery, knowledgeGraph, memory_context=None):
        # Query relevant macro data from the knowledge graph
        macro_facts = knowledgeGraph.query(subject_type="EconomicIndicator")
        market_data = knowledgeGraph.query(subject_type="MarketIndicator")
        memory_context = memory_context or {}
        previous_scores = memory_context.get("performance_history", [])
        avg_score = sum(previous_scores) / len(previous_scores) if previous_scores else 0.0
        
        # Structured reasoning process
        reasoning_steps = [
            {
                "step": "Analyze interest rate trends",
                "data": "Federal funds rate increased by 25 basis points",
                "source": self.sources["fed_data"],
                "inference": "Monetary policy is tightening"
            },
            {
                "step": "Evaluate market volatility",
                "data": "VIX index above 20 for past 30 days",
                "source": self.sources["market_indices"],
                "inference": "Market uncertainty is elevated"
            },
            {
                "step": "Assess inflation indicators",
                "data": "CPI at 3.2%, above Fed target of 2%",
                "source": self.sources["inflation_reports"],
                "inference": "Inflation remains a concern for policymakers"
            }
        ]
        
        # Generate conclusion based on reasoning steps
        conclusion = self._synthesize_conclusion(reasoning_steps)
        
        # Return structured output with reasoning path and sources
        return {
            "subquery": subquery,
            "timestamp": datetime.datetime.now().isoformat(),
            "reasoningPath": reasoning_steps,
            "sources": self.sources,
            "conclusion": conclusion,
            "confidence": 0.85,
            "relevantMetrics": {
                "interest_rate": "4.75%",
                "inflation": "3.2%",
                "market_volatility": "high",
                "memory_avg_score": round(avg_score, 4),
            },
            "memory_context_used": {
                "past_round_count": len(memory_context.get("past_round_cids", [])),
                "recent_performance_points": len(previous_scores),
            },
        }
    
    def _synthesize_conclusion(self, reasoning_steps):
        """Generate a conclusion based on reasoning steps"""
        # In a real implementation, this would use more sophisticated logic
        # or potentially call an LLM to synthesize the conclusion
        return "Macro conditions suggest caution in investment strategy due to tightening monetary policy, elevated market uncertainty, and persistent inflation concerns."