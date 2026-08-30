from unittest.mock import patch, MagicMock
from scanner.registry import scan_host


@patch("scanner.registry._SCANNERS")
def test_scan_host_dispatches_to_ssh(mock_scanners):
    mock_scanner = MagicMock(return_value={"os": "RHEL 9.3"})
    mock_scanners.__getitem__ = MagicMock(return_value=mock_scanner)
    mock_scanners.__contains__ = MagicMock(return_value=True)

    cred = MagicMock()
    result = scan_host("10.0.1.1", 22, cred, "ssh_network", "quick")
    mock_scanner.assert_called_once_with("10.0.1.1", 22, cred, "quick")
    assert result["os"] == "RHEL 9.3"


def test_scan_host_unknown_type():
    cred = MagicMock()
    try:
        scan_host("x", 22, cred, "unknown_type", "quick")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "unknown_type" in str(e)
