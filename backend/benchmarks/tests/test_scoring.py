import pytest
from unittest.mock import MagicMock
from benchmarks.scoring import score_scan_results


def _make_result(status="success", **data_overrides):
    r = MagicMock()
    r.status = status
    default_data = {
        "os": "Red Hat Enterprise Linux 9.3",
        "os_id": "rhel",
        "os_version": "9.3",
        "selinux_status": "Enforcing",
        "firewall_active": True,
        "fips_enabled": False,
        "pending_updates": 0,
        "root_login_disabled": True,
        "audit_logging": True,
        "crypto_policy": "DEFAULT",
        "products": ["RHEL"],
        "subscriptions": ["Red Hat Enterprise Linux Server"],
    }
    default_data.update(data_overrides)
    r.data = default_data
    return r


def test_score_all_passing():
    results = [_make_result() for _ in range(3)]
    scores = score_scan_results(results)
    assert scores["overall_score"] > 0
    assert "categories" in scores
    assert "linux" in scores["categories"]
    linux = scores["categories"]["linux"]
    assert linux["score"] > 50
    assert linux["industry_average"] == 62
    assert linux["checks"]["selinux_enforcing"]["passed"] is True


def test_score_with_failures():
    results = [
        _make_result(selinux_status="Disabled", firewall_active=False, pending_updates=20),
    ]
    scores = score_scan_results(results)
    linux = scores["categories"]["linux"]
    assert linux["checks"]["selinux_enforcing"]["passed"] is False
    assert linux["checks"]["firewall_active"]["passed"] is False
    assert linux["checks"]["patches_current"]["passed"] is False


def test_score_empty_results():
    scores = score_scan_results([])
    assert scores["overall_score"] == 0
    linux = scores["categories"]["linux"]
    assert linux["score"] == 0


def test_score_includes_all_categories():
    results = [_make_result()]
    scores = score_scan_results(results)
    assert set(scores["categories"].keys()) == {"linux", "automation", "kubernetes", "third_party"}
