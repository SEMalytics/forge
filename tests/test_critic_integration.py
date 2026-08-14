"""
Tests for MultiLLMCritic integration in ReviewLayer (KF 7.26).

All tests use mocks — no live API calls and no sentence-transformer downloads.
Heavy ReviewLayer internals (FailureAnalyzer, FixGenerator, TestingOrchestrator,
TriageWorkflow) are patched so tests stay fast and offline.
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from forge.layers.critic import CritiqueResult, Finding, MultiLLMCritic
from forge.layers.review import ReviewLayer, ReviewSummary


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_HEAVY_PATCHES = [
    "forge.layers.review.FailureAnalyzer",
    "forge.layers.review.FixGenerator",
    "forge.layers.review.TestingOrchestrator",
    "forge.layers.review.TriageWorkflow",
]


def _patched_layer(tmp_path: Path, **kwargs) -> ReviewLayer:
    """Construct ReviewLayer with all heavy internals mocked."""
    mocks = {p: MagicMock() for p in _HEAVY_PATCHES}
    with patch.multiple("forge.layers.review", **{
        p.split(".")[-1]: mocks[p] for p in _HEAVY_PATCHES
    }):
        layer = ReviewLayer(learning_db_path=tmp_path / "learn.json", **kwargs)
    return layer


def _make_critique_result(confirmed: int = 0, single: int = 0) -> CritiqueResult:
    findings = []
    for i in range(confirmed):
        findings.append(Finding(
            description=f"Confirmed finding {i}",
            severity=1,
            severity_label="Critical",
            location="main.py",
            model_sources=["claude", "openai"],
        ))
    for i in range(single):
        findings.append(Finding(
            description=f"Single finding {i}",
            severity=2,
            severity_label="High",
            location="main.py",
            model_sources=["claude"],
        ))
    return CritiqueResult(
        findings=findings,
        models_used=["claude", "openai"],
        confirmed_count=confirmed,
        single_model_count=single,
    )


def _mock_critic(confirmed: int = 0, single: int = 0) -> MagicMock:
    critic = MagicMock(spec=MultiLLMCritic)
    critic.critique = AsyncMock(return_value=_make_critique_result(confirmed, single))
    return critic


def _passing_test_report():
    from forge.layers.testing import ComprehensiveTestReport
    from forge.testing.docker_runner import ExecutionResult, SupportedFramework

    unit = ExecutionResult(framework=SupportedFramework.PYTEST)
    unit.passed = 1
    unit.failed = 0
    unit.output = "1 passed"
    return ComprehensiveTestReport(
        project_id="test-proj",
        unit_test_result=unit,
        all_passed=True,
        security_passed=True,
        passed_tests=1,
        failed_tests=0,
    )


# ---------------------------------------------------------------------------
# Unit tests — ReviewLayer init
# ---------------------------------------------------------------------------


class TestReviewLayerCriticInit:
    def test_critic_injected_when_provided(self, tmp_path):
        mock = _mock_critic()
        layer = _patched_layer(tmp_path, critic=mock)
        assert layer._critic is mock

    def test_critic_disabled_by_flag(self, tmp_path):
        mock = _mock_critic()
        layer = _patched_layer(tmp_path, enable_adversarial_critic=False, critic=mock)
        assert layer._critic is None

    def test_critic_attr_always_present(self, tmp_path):
        """ReviewLayer must always expose _critic (may be None)."""
        layer = _patched_layer(tmp_path)
        assert hasattr(layer, "_critic")

    def test_critic_none_when_no_key_and_no_injection(self, tmp_path):
        """If ANTHROPIC_API_KEY is absent, critic silently stays None."""
        with patch("forge.layers.critic.MultiLLMCritic") as MockClass:
            from forge.layers.critic import CriticError
            MockClass.side_effect = CriticError("no key")
            layer = _patched_layer(tmp_path, enable_adversarial_critic=True)
        assert layer._critic is None


# ---------------------------------------------------------------------------
# Unit tests — _run_adversarial_critique
# ---------------------------------------------------------------------------


class TestRunAdversarialCritique:
    @pytest.mark.asyncio
    async def test_returns_none_when_critic_is_none(self, tmp_path):
        layer = _patched_layer(tmp_path, enable_adversarial_critic=False)
        result = await layer._run_adversarial_critique({"main.py": "x = 1"})
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_critique_result_on_success(self, tmp_path):
        mock = _mock_critic(confirmed=1)
        layer = _patched_layer(tmp_path, critic=mock)
        result = await layer._run_adversarial_critique(
            {"main.py": "x = 1"}, project_context="test"
        )
        assert isinstance(result, CritiqueResult)
        assert result.confirmed_count == 1

    @pytest.mark.asyncio
    async def test_passes_combined_content_to_critic(self, tmp_path):
        mock = _mock_critic()
        layer = _patched_layer(tmp_path, critic=mock)
        files = {"a.py": "x = 1", "b.py": "y = 2"}
        await layer._run_adversarial_critique(files)

        called_content: str = mock.critique.call_args[0][0]
        assert "# File: a.py" in called_content
        assert "# File: b.py" in called_content
        assert "x = 1" in called_content
        assert "y = 2" in called_content

    @pytest.mark.asyncio
    async def test_returns_none_on_exception(self, tmp_path):
        mock = MagicMock(spec=MultiLLMCritic)
        mock.critique = AsyncMock(side_effect=RuntimeError("network error"))
        layer = _patched_layer(tmp_path, critic=mock)
        result = await layer._run_adversarial_critique({"f.py": "pass"})
        assert result is None


# ---------------------------------------------------------------------------
# Unit tests — ReviewSummary
# ---------------------------------------------------------------------------


class TestReviewSummaryCritiqueResult:
    def test_review_summary_has_critique_result_field(self):
        summary = ReviewSummary(
            project_id="test",
            total_iterations=1,
            final_status="passed",
            iterations=[],
            total_duration_seconds=1.0,
        )
        assert hasattr(summary, "critique_result")
        assert summary.critique_result is None

    def test_review_summary_stores_critique_result(self):
        critique = _make_critique_result(confirmed=1)
        summary = ReviewSummary(
            project_id="test",
            total_iterations=1,
            final_status="passed",
            iterations=[],
            total_duration_seconds=1.0,
            critique_result=critique,
        )
        assert summary.critique_result is critique

    def test_to_dict_includes_adversarial_critique(self):
        critique = _make_critique_result(confirmed=1, single=2)
        summary = ReviewSummary(
            project_id="test",
            total_iterations=1,
            final_status="passed",
            iterations=[],
            total_duration_seconds=1.0,
            critique_result=critique,
        )
        d = summary.to_dict()
        assert "adversarial_critique" in d
        assert d["adversarial_critique"]["confirmed_count"] == 1
        assert d["adversarial_critique"]["single_model_count"] == 2

    def test_to_dict_adversarial_critique_none_when_no_critique(self):
        summary = ReviewSummary(
            project_id="test",
            total_iterations=1,
            final_status="passed",
            iterations=[],
            total_duration_seconds=1.0,
        )
        d = summary.to_dict()
        assert d["adversarial_critique"] is None


# ---------------------------------------------------------------------------
# Integration — critique fires before test loop
# ---------------------------------------------------------------------------


class TestAdversarialCritiqueInLoop:
    """
    Verify critique runs before tests and its result lands in the summary.
    TestingOrchestrator is mocked to return a passing report immediately.
    """

    @pytest.mark.asyncio
    async def test_critique_result_in_passed_summary(self, tmp_path):
        mock_critic = _mock_critic(confirmed=1)
        layer = _patched_layer(tmp_path, critic=mock_critic)
        layer.test_orchestrator.test_project = AsyncMock(return_value=_passing_test_report())

        summary = await layer.iterate_until_passing(
            project_id="test-proj",
            code_files={"main.py": "x = 1"},
            output_dir=tmp_path / "out",
            max_iterations=1,
        )

        assert isinstance(summary, ReviewSummary)
        assert summary.critique_result is not None
        assert summary.critique_result.confirmed_count == 1

    @pytest.mark.asyncio
    async def test_critique_runs_once_regardless_of_iterations(self, tmp_path):
        mock_critic = _mock_critic()
        layer = _patched_layer(tmp_path, critic=mock_critic)
        layer.test_orchestrator.test_project = AsyncMock(return_value=_passing_test_report())

        await layer.iterate_until_passing(
            project_id="test-proj",
            code_files={"main.py": "x = 1"},
            output_dir=tmp_path / "out",
            max_iterations=3,
        )

        # Critique is called once before the loop, not per-iteration
        assert mock_critic.critique.call_count == 1

    @pytest.mark.asyncio
    async def test_no_critique_when_disabled(self, tmp_path):
        mock_critic = _mock_critic()
        layer = _patched_layer(tmp_path, enable_adversarial_critic=False, critic=mock_critic)
        layer.test_orchestrator.test_project = AsyncMock(return_value=_passing_test_report())

        summary = await layer.iterate_until_passing(
            project_id="test-proj",
            code_files={"main.py": "x = 1"},
            output_dir=tmp_path / "out",
            max_iterations=1,
        )

        mock_critic.critique.assert_not_called()
        assert summary.critique_result is None
