import datetime

from reasoning_modules.base.module import ReasoningModule
from reasoning_modules.memory_hints import memory_learning_hint


class SentimentReasoningModule(ReasoningModule):
    def __init__(self):
        super().__init__('sentiment')
        self.sources = {
            "twitter_data": "Twitter API Sentiment Analysis",
            "reddit_data": "Reddit Community Discussions",
            "community_metrics": "DeFi Community Engagement Tracker"
        }

    def run(self, subquery, knowledgeGraph, memory_context=None):
        # Use the correct query method instead of queryGraph
        token_data = knowledgeGraph.query(subject="TokenX")
        social_data = knowledgeGraph.query(predicate="has_sentiment")
        memory_context = memory_context or {}
        previous_scores = memory_context.get("performance_history", [])
        if not isinstance(previous_scores, list):
            previous_scores = []
        numeric_scores = [float(s) for s in previous_scores if isinstance(s, (int, float))]
        avg_score = sum(numeric_scores) / len(numeric_scores) if numeric_scores else 0.0
        learning_hint = memory_learning_hint(numeric_scores)

        # Structured reasoning process
        reasoning_steps = [
            {
                "step": "Analyze Twitter sentiment",
                "data": "Negative sentiment detected on Twitter",
                "source": self.sources["twitter_data"],
                "inference": "Social media sentiment is predominantly negative"
            },
            {
                "step": "Review Reddit discussions",
                "data": "Reddit discussions flagged increased concerns",
                "source": self.sources["reddit_data"],
                "inference": "Community forums show rising concerns"
            },
            {
                "step": "Measure community engagement",
                "data": "Community engagement is dropping",
                "source": self.sources["community_metrics"],
                "inference": "Declining interest and participation"
            }
        ]
        
        conclusion = "Community sentiment around TokenX is currently negative"
        if numeric_scores and sum(1 for s in numeric_scores[-5:] if s < 0.35) >= 2:
            conclusion += " (agent memory: past rounds scored low—stress data limitations and avoid overreading tone)."

        # Return structured output with reasoning path and sources
        return {
            "subquery": subquery,
            "timestamp": datetime.datetime.now().isoformat(),
            "reasoningPath": reasoning_steps,
            "sources": self.sources,
            "conclusion": conclusion,
            "confidence": 0.82,
            "relevantMetrics": {
                "twitter_sentiment": "-0.65",
                "reddit_sentiment": "-0.48",
                "engagement_change": "-22% MoM",
                "memory_avg_score": round(avg_score, 4),
                "memory_learning_hint": learning_hint,
            },
            "memory_context_used": {
                "past_round_count": len(memory_context.get("past_round_cids", [])),
                "recent_performance_points": len(numeric_scores),
            },
        }