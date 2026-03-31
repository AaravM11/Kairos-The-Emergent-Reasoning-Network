class ReasoningModule:
    """
    Pluggable reasoning agent. Subclasses implement ``run`` with optional kwargs:
    ``openai_key`` (e.g. DeFi), ``memory_context`` (past CIDs and scores from IPFS).
    """

    def __init__(self, name: str) -> None:
        self.name = name

    def run(self, subquery, knowledgeGraph, **kwargs):
        raise NotImplementedError("Subclasses must implement the run() method.")
