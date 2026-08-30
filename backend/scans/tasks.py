from django.utils import timezone
from huey.contrib.djhuey import task
from scanner.registry import scan_host


@task()
def run_scan(scan_id: int) -> None:
    from scans.models import Scan, ScanResult

    scan = Scan.objects.get(id=scan_id)
    scan.status = "running"
    scan.started_at = timezone.now()

    all_hosts = []
    for source in scan.sources.all():
        for host in source.hosts:
            all_hosts.append((host, source))

    scan.progress = {
        "total_hosts": len(all_hosts),
        "completed_hosts": 0,
        "found_systems": 0,
        "current_source": "",
    }
    scan.save()

    for host, source in all_hosts:
        scan.progress["current_source"] = source.name
        scan.save()

        try:
            data = scan_host(
                host=host,
                port=source.port,
                credential=source.credential,
                source_type=source.source_type,
                scan_type=scan.scan_type,
            )
            ScanResult.objects.create(
                scan=scan, host=host, source=source, status="success", data=data,
            )
            scan.progress["found_systems"] += 1
        except Exception as e:
            ScanResult.objects.create(
                scan=scan, host=host, source=source, status="failed", error_message=str(e),
            )

        scan.progress["completed_hosts"] += 1
        scan.save()

    scan.status = "completed"
    scan.completed_at = timezone.now()
    scan.save()
