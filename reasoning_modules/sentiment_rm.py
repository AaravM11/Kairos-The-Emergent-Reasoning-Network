from reasoning_modules.base.module import ReasoningModule
import datetime

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
        avg_score = sum(previous_scores) / len(previous_scores) if previous_scores else 0.0
        
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
        
        # Return structured output with reasoning path and sources
        return {
            "subquery": subquery,
            "timestamp": datetime.datetime.now().isoformat(),
            "reasoningPath": reasoning_steps,
            "sources": self.sources,
            "conclusion": "Community sentiment around TokenX is currently negative",
            "confidence": 0.82,
            "relevantMetrics": {
                "twitter_sentiment": "-0.65",
                "reddit_sentiment": "-0.48",
                "engagement_change": "-22% MoM",
                "memory_avg_score": round(avg_score, 4),
            },
            "memory_context_used": {
                "past_round_count": len(memory_context.get("past_round_cids", [])),
                "recent_performance_points": len(previous_scores),
            },
        }