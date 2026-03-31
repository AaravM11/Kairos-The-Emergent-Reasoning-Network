import json
import os
import sys
import tempfile
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.knowledge_graph.knowledgeGraph import KnowledgeGraph
from core.orchestrator.index import orchestrate


class IntegrationTest(unittest.TestCase):
    def setUp(self) -> None:
        os.environ["KAIROS_FAKE_IPFS"] = "1"
        self._reg_fd, self._reg_path = tempfile.mkstemp(suffix="kairos-registry.json")
        os.close(self._reg_fd)
        with open(self._reg_path, "w", encoding="utf-8") as fp:
            json.dump({}, fp)
        os.environ["AGENT_MEMORY_REGISTRY_PATH"] = self._reg_path
        self.kg = KnowledgeGraph()

    def tearDown(self) -> None:
        os.environ.pop("KAIROS_FAKE_IPFS", None)
        os.environ.pop("AGENT_MEMORY_REGISTRY_PATH", None)
        try:
            os.remove(self._reg_path)
        except OSError:
            pass

    def test_marketplace_structure_without_validation(self) -> None:
        """Cheap path: multi-agent round, fake IPFS, confidence-based scores."""
        query = "What are the risks of investing in Ethereum?"
        result = orchestrate(
            query=query,
            knowledge_graph=self.kg,
            openai_key=None,
            run_validation=False,
        )
        self.assertIsNone(result.get("error"), msg=result.get("error"))
        self.assertTrue(result.get("competition"))
        self.assertIn("winner", result)
        self.assertIn("reasoning_round_cid", result)
        self.assertTrue(str(result["reasoning_round_cid"]).startswith("sha256-"))
        winner = result.get("winner")
        self.assertIsNotNone(winner)
        for row in result["competition"]:
            self.assertIn("module_name", row)
            self.assertIn("score", row)
            self.assertIn("output", row)

    def test_end_to_end_with_openai_validation(self) -> None:
        """Full validators (including alignment); requires OPENAI_API_KEY and network."""
        openai_key = os.environ.get("OPENAI_API_KEY")
        if not openai_key:
            self.skipTest("OPENAI_API_KEY not set")

        query = "Summarize key risks in two sentences."
        result = orchestrate(
            query=query,
            knowledge_graph=self.kg,
            openai_key=openai_key,
            run_validation=True,
            alignment_profile={"preferences": "Favor cautious, factual answers."},
        )
        self.assertIsNone(result.get("error"), msg=result.get("error"))
        self.assertIsNotNone(result.get("reasoning"))
        out = result["reasoning"]
        self.assertTrue(out.get("conclusion") or out.get("answer"))
        val = result.get("validation") or {}
        self.assertIn("logical", val)
        self.assertIn("grounding", val)
        self.assertIn("alignment", val)
        for row in result.get("competition", []):
            metrics = row.get("metrics") or {}
            self.assertIn("alignment", metrics)


if __name__ == "__main__":
    unittest.main()
