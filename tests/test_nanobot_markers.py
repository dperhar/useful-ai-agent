import re
import unittest

from modules.nanobot.patches import patch_nanobot_effort


class NanobotMarkerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        namespace: dict[str, object] = {"re": re}
        exec("from __future__ import annotations\n" + patch_nanobot_effort.HELPER, namespace)
        cls.extract_effort = staticmethod(namespace["_useful_agent_extract_one_turn_reasoning_effort"])
        cls.expand = staticmethod(namespace["_useful_agent_expand_command_shortcuts"])

    def test_improve_exact_marker_anywhere(self) -> None:
        result = self.expand("please /improve this answer")
        self.assertEqual(result, "Use the improve skill on this request/output. please this answer")

    def test_improve_bot_suffix_is_not_shortcut(self) -> None:
        result = self.expand("please /improve@schnyr_bot this answer")
        self.assertEqual(result, "please /improve@schnyr_bot this answer")

    def test_goal_exact_marker_becomes_codex_native_command(self) -> None:
        result = self.expand("make roadmap /goal for this harness")
        self.assertEqual(result, "/goal make roadmap for this harness")

    def test_goal_bot_suffix_is_not_shortcut(self) -> None:
        result = self.expand("make roadmap /goal@schnyr_bot for this harness")
        self.assertEqual(result, "make roadmap /goal@schnyr_bot for this harness")

    def test_xhigh_and_improve_coexist(self) -> None:
        effort, cleaned = self.extract_effort("xhigh /improve improve this plan")
        self.assertEqual(effort, "xhigh")
        self.assertEqual(cleaned, "/improve improve this plan")
        self.assertEqual(
            self.expand(cleaned),
            "Use the improve skill on this request/output. improve this plan",
        )


if __name__ == "__main__":
    unittest.main()
