from collections import defaultdict
from .standards import INDUSTRY_AVERAGES, RHEL_SUPPORTED_VERSIONS, OPENSHIFT_SUPPORTED_VERSIONS


def score_scan_results(results) -> dict:
    categories = {}
    for key, standard in INDUSTRY_AVERAGES.items():
        check_results = _evaluate_category(key, results)
        earned = sum(
            standard["checks"][check]["weight"]
            for check, passed in check_results.items()
            if passed
        )
        total = sum(c["weight"] for c in standard["checks"].values())
        score = round((earned / total) * 100) if total > 0 else 0

        categories[key] = {
            "label": standard["label"],
            "description": standard["description"],
            "score": score,
            "industry_average": standard["average_score"],
            "checks": {
                check: {
                    "label": standard["checks"][check]["label"],
                    "passed": passed,
                    "source": standard["checks"][check]["source"],
                    "weight": standard["checks"][check]["weight"],
                }
                for check, passed in check_results.items()
            },
        }

    overall = round(sum(c["score"] for c in categories.values()) / len(categories)) if categories else 0
    overall_avg = round(sum(c["industry_average"] for c in categories.values()) / len(categories)) if categories else 0

    return {
        "overall_score": overall,
        "overall_industry_average": overall_avg,
        "categories": categories,
    }


def _evaluate_category(category: str, results) -> dict:
    if category == "linux":
        return _evaluate_linux(results)
    elif category == "automation":
        return _evaluate_automation(results)
    elif category == "kubernetes":
        return _evaluate_kubernetes(results)
    elif category == "third_party":
        return _evaluate_third_party(results)
    return {}


def _evaluate_linux(results) -> dict:
    successful = [r for r in results if r.status == "success"]
    if not successful:
        return {k: False for k in INDUSTRY_AVERAGES["linux"]["checks"]}

    selinux_count = sum(1 for r in successful if r.data.get("selinux_status") == "Enforcing")
    firewall_count = sum(1 for r in successful if r.data.get("firewall_active"))
    fips_count = sum(1 for r in successful if r.data.get("fips_enabled"))
    patched_count = sum(1 for r in successful if r.data.get("pending_updates", -1) == 0)
    root_disabled = sum(1 for r in successful if r.data.get("root_login_disabled"))
    audit_count = sum(1 for r in successful if r.data.get("audit_logging"))
    crypto_count = sum(1 for r in successful if r.data.get("crypto_policy", "").upper() in ("DEFAULT", "FUTURE", "FIPS"))

    n = len(successful)
    threshold = 0.7

    return {
        "selinux_enforcing": (selinux_count / n) >= threshold,
        "firewall_active": (firewall_count / n) >= threshold,
        "fips_enabled": (fips_count / n) >= threshold,
        "patches_current": (patched_count / n) >= threshold,
        "root_login_disabled": (root_disabled / n) >= threshold,
        "audit_logging": (audit_count / n) >= threshold,
        "crypto_policy_modern": (crypto_count / n) >= threshold,
    }


def _evaluate_automation(results) -> dict:
    successful = [r for r in results if r.status == "success"]
    all_products = []
    for r in successful:
        all_products.extend(r.data.get("products", []))

    has_aap = any("Ansible" in p or "AAP" in p for p in all_products)
    has_ansible = has_aap or any("ansible" in r.data.get("os", "").lower() for r in successful)
    has_satellite = any("Satellite" in p for p in all_products)
    has_subscription = any(r.data.get("subscriptions") for r in successful)

    return {
        "aap_present": has_aap,
        "ansible_detected": has_ansible,
        "managed_by_satellite": has_satellite,
        "subscription_active": has_subscription,
    }


def _evaluate_kubernetes(results) -> dict:
    successful = [r for r in results if r.status == "success"]
    all_products = []
    for r in successful:
        all_products.extend(r.data.get("products", []))

    has_openshift = any("OpenShift" in p for p in all_products)
    cluster_current = False
    nodes_healthy = False
    runtime_current = False

    for r in successful:
        cv = r.data.get("cluster_version", "")
        if cv:
            version_short = ".".join(cv.lstrip("v").split(".")[:2])
            cluster_current = version_short in OPENSHIFT_SUPPORTED_VERSIONS
            nodes = r.data.get("nodes", [])
            if nodes:
                nodes_healthy = True
                runtime_current = True

    return {
        "openshift_present": has_openshift,
        "cluster_version_current": cluster_current,
        "node_health": nodes_healthy,
        "container_runtime_current": runtime_current,
    }


def _evaluate_third_party(results) -> dict:
    successful = [r for r in results if r.status == "success"]
    if not successful:
        return {k: False for k in INDUSTRY_AVERAGES["third_party"]["checks"]}

    supported_count = 0
    subscription_count = 0
    patched_count = 0
    certified_count = 0

    for r in successful:
        os_version = r.data.get("os_version", "")
        major = os_version.split(".")[0] if os_version else ""
        if major in RHEL_SUPPORTED_VERSIONS:
            supported_count += 1

        if r.data.get("subscriptions"):
            subscription_count += 1

        if r.data.get("pending_updates", -1) <= 5:
            patched_count += 1

        products = r.data.get("products", [])
        if any(p in ("RHEL", "Satellite", "Ansible", "OpenShift") for p in products):
            certified_count += 1

    n = len(successful)
    threshold = 0.6

    return {
        "supported_os_version": (supported_count / n) >= threshold,
        "subscription_compliant": (subscription_count / n) >= threshold,
        "vulnerability_patched": (patched_count / n) >= threshold,
        "certified_products": (certified_count / n) >= threshold,
    }
