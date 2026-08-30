from unittest.mock import patch, MagicMock
from scanner.ssh import scan, _parse_os_release


def test_parse_os_release_rhel():
    content = 'NAME="Red Hat Enterprise Linux"\nVERSION="9.3 (Plow)"\nID=rhel\nVERSION_ID="9.3"\n'
    result = _parse_os_release(content)
    assert result["name"] == "Red Hat Enterprise Linux"
    assert result["version"] == "9.3 (Plow)"
    assert result["id"] == "rhel"


def test_parse_os_release_centos():
    content = 'NAME="CentOS Stream"\nVERSION="9"\nID=centos\n'
    result = _parse_os_release(content)
    assert result["name"] == "CentOS Stream"
    assert result["id"] == "centos"


@patch("scanner.ssh._ssh_exec")
def test_scan_quick(mock_exec):
    mock_exec.side_effect = [
        'NAME="Red Hat Enterprise Linux"\nVERSION="9.3"\nID=rhel\nVERSION_ID="9.3"\n',  # os-release
        "server1.example.com",  # hostname
        "5.14.0-362.el9.x86_64",  # uname -r
        "x86_64",  # uname -m
        "4",  # nproc
        "8192000",  # meminfo MemTotal (kB)
    ]
    cred = MagicMock()
    cred.credential_type = "password"
    cred.username = "root"
    cred.get_secret.return_value = "password"

    result = scan("10.0.1.1", 22, cred, "quick")
    assert result["hostname"] == "server1.example.com"
    assert result["os"] == "Red Hat Enterprise Linux 9.3"
    assert result["kernel"] == "5.14.0-362.el9.x86_64"
    assert result["cpu_count"] == 4
