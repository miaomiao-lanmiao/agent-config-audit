"""Fail-closed release configuration check; does not publish anything."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from typing import Any


def validate_environment(data: dict[str, Any]) -> list[str]:
    errors = []
    rules = data.get("protection_rules", [])
    if not isinstance(rules, list) or not any(
        isinstance(rule, dict) and rule.get("type") == "required_reviewers" and rule.get("reviewers") for rule in rules
    ):
        errors.append("pypi-release must have at least one required reviewer.")
    policy = data.get("deployment_branch_policy") or {}
    if not policy.get("custom_branch_policies"):
        errors.append("pypi-release must restrict deployment branches to a custom main-only policy.")
    return errors


def validate_branches(data: dict[str, Any]) -> list[str]:
    policies = data.get("branch_policies", [])
    if len(policies) != 1 or policies[0].get("name") != "main" or policies[0].get("type", "branch") != "branch":
        return ["pypi-release must allow exactly the main branch (no tags or wildcard branches)."]
    return []


def _api(path: str) -> dict[str, Any]:
    result = subprocess.run(["gh", "api", path], capture_output=True, text=True, timeout=30)
    if result.returncode:
        raise RuntimeError("Cannot verify GitHub release environment; publication is blocked.")
    data = json.loads(result.stdout)
    if not isinstance(data, dict):
        raise RuntimeError("Unexpected GitHub metadata; publication is blocked.")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""))
    args = parser.parse_args()
    if not args.repo or len(args.repo.split("/")) != 2:
        print("BLOCKED: supply --repo OWNER/REPO or GITHUB_REPOSITORY.")
        return 2
    try:
        endpoint = f"repos/{args.repo}/environments/pypi-release"
        errors = validate_environment(_api(endpoint)) + validate_branches(
            _api(endpoint + "/deployment-branch-policies")
        )
    except (OSError, subprocess.TimeoutExpired, RuntimeError, ValueError, TypeError, KeyError):
        print("BLOCKED: release environment could not be verified. No publication attempted.")
        return 2
    for error in errors:
        print(f"BLOCKED: {error}")
    if errors:
        return 1
    print("Environment reviewers and main-only branch policy verified. PyPI OIDC trust must also be configured.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
