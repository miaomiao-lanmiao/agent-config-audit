from __future__ import annotations

import unittest

from tools.release_preflight import validate_branches, validate_environment


class ReleaseGateTests(unittest.TestCase):
    def test_missing_gate_fails_closed(self) -> None:
        self.assertTrue(validate_environment({}))
        self.assertTrue(validate_environment({"protection_rules": []}))

    def test_empty_reviewer_list_rejected(self) -> None:
        self.assertTrue(validate_environment({"protection_rules": [{"type": "required_reviewers", "reviewers": []}]}))

    def test_valid_reviewers_and_branch_policy(self) -> None:
        self.assertEqual(
            validate_environment(
                {
                    "protection_rules": [{"type": "required_reviewers", "reviewers": [{"type": "User", "id": 1}]}],
                    "deployment_branch_policy": {"custom_branch_policies": True},
                }
            ),
            [],
        )

    def test_missing_or_wildcard_branch_rejected(self) -> None:
        for policies in ([], [{"name": "*"}], [{"name": "main", "type": "tag"}], [{"name": "main"}, {"name": "other"}]):
            self.assertTrue(validate_branches({"branch_policies": policies}))

    def test_only_main_allowed(self) -> None:
        self.assertEqual(validate_branches({"branch_policies": [{"name": "main", "type": "branch"}]}), [])
