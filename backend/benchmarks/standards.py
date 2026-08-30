INDUSTRY_AVERAGES = {
    "linux": {
        "label": "Linux (RHEL)",
        "description": "Security hardening and system management based on CIS Benchmark for RHEL and Red Hat Security Guide",
        "average_score": 62,
        "checks": {
            "selinux_enforcing": {"weight": 20, "label": "SELinux Enforcing", "source": "CIS RHEL 9 Benchmark 1.6.1"},
            "firewall_active": {"weight": 15, "label": "Firewall Active", "source": "CIS RHEL 9 Benchmark 3.4.1"},
            "fips_enabled": {"weight": 10, "label": "FIPS Mode Enabled", "source": "NIST SP 800-171"},
            "patches_current": {"weight": 20, "label": "System Patches Current", "source": "Red Hat RHSA Advisory Compliance"},
            "root_login_disabled": {"weight": 15, "label": "Root SSH Disabled", "source": "CIS RHEL 9 Benchmark 5.2.10"},
            "audit_logging": {"weight": 10, "label": "Audit Logging Active", "source": "CIS RHEL 9 Benchmark 4.1.1"},
            "crypto_policy_modern": {"weight": 10, "label": "Modern Crypto Policy", "source": "Red Hat Crypto Policies Guide"},
        },
    },
    "automation": {
        "label": "Automation (Ansible)",
        "description": "Ansible Automation Platform adoption and best practices based on Red Hat AAP guidelines",
        "average_score": 48,
        "checks": {
            "aap_present": {"weight": 30, "label": "AAP Deployed", "source": "Red Hat AAP Best Practices"},
            "ansible_detected": {"weight": 20, "label": "Ansible Installed", "source": "Red Hat AAP Planning Guide"},
            "managed_by_satellite": {"weight": 25, "label": "Centrally Managed", "source": "Red Hat Smart Management"},
            "subscription_active": {"weight": 25, "label": "Active Subscription", "source": "Red Hat Subscription Management"},
        },
    },
    "kubernetes": {
        "label": "Kubernetes (OpenShift)",
        "description": "Container platform security and adoption based on CIS Kubernetes Benchmark and OpenShift security guide",
        "average_score": 44,
        "checks": {
            "openshift_present": {"weight": 30, "label": "OpenShift Deployed", "source": "Red Hat OpenShift Platform Plus"},
            "cluster_version_current": {"weight": 25, "label": "Cluster Version Current", "source": "Red Hat OpenShift Lifecycle"},
            "node_health": {"weight": 25, "label": "All Nodes Healthy", "source": "CIS Kubernetes Benchmark 4.1"},
            "container_runtime_current": {"weight": 20, "label": "Container Runtime Current", "source": "Red Hat Container Health Index"},
        },
    },
    "third_party": {
        "label": "3rd Party Applications",
        "description": "Software lifecycle management and vulnerability posture based on Red Hat Product Security data",
        "average_score": 58,
        "checks": {
            "supported_os_version": {"weight": 30, "label": "Supported OS Version", "source": "Red Hat Product Life Cycle"},
            "subscription_compliant": {"weight": 25, "label": "Subscription Compliant", "source": "Red Hat Subscription Management"},
            "vulnerability_patched": {"weight": 25, "label": "Known CVEs Patched", "source": "Red Hat Product Security Center"},
            "certified_products": {"weight": 20, "label": "Using Certified Software", "source": "Red Hat Ecosystem Catalog"},
        },
    },
}

RHEL_SUPPORTED_VERSIONS = ["7", "8", "9"]
OPENSHIFT_SUPPORTED_VERSIONS = ["4.12", "4.13", "4.14", "4.15", "4.16"]
