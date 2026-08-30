import { useEffect, useState } from "react";
import {
  TextContent,
  Text,
  Button,
  Card,
  CardBody,
  Gallery,
  Spinner,
  Alert,
} from "@patternfly/react-core";
import { useNavigate } from "react-router-dom";
import { apiClient } from "../api/client";
import { WizardData } from "./types";

interface Report {
  id: number;
  title: string;
  summary: {
    total_hosts: number;
    successful_hosts: number;
    failed_hosts: number;
    os_distribution: Record<string, number>;
    products_found: Record<string, number>;
  };
}

interface StepResultsProps {
  data: WizardData;
  onUpdate: (data: Partial<WizardData>) => void;
  onReset: () => void;
}

export function StepResults({ data, onUpdate, onReset }: StepResultsProps) {
  const [report, setReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    if (data.scan_id) {
      apiClient
        .get<{ report: { id: number } }>(`/scans/${data.scan_id}/`)
        .then((scan) => {
          if (scan.report) {
            return apiClient.get<Report>(`/reports/${scan.report.id}/`);
          }
          return apiClient.get<Report[]>("/reports/").then((reports) => reports[0]);
        })
        .then((r) => {
          if (r) {
            setReport(r);
            onUpdate({ report_id: r.id });
          }
        })
        .catch(() => {})
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, [data.scan_id]);

  if (loading) return <Spinner size="xl" />;

  if (!report) return <Alert variant="warning" isInline title="No report found. Please run a scan first." />;

  const { summary } = report;

  return (
    <TextContent>
      <Text component="h2">Health Check Results</Text>

      <Gallery hasGutter minWidths={{ default: "200px" }}>
        <Card isCompact>
          <CardBody>
            <Text component="h3">{summary.total_hosts}</Text>
            <Text component="small">Total Hosts Scanned</Text>
          </CardBody>
        </Card>
        <Card isCompact>
          <CardBody>
            <Text component="h3">{summary.successful_hosts}</Text>
            <Text component="small">Successful</Text>
          </CardBody>
        </Card>
        <Card isCompact>
          <CardBody>
            <Text component="h3">{summary.failed_hosts}</Text>
            <Text component="small">Failed</Text>
          </CardBody>
        </Card>
      </Gallery>

      <Text component="h3">Operating Systems Found</Text>
      {Object.entries(summary.os_distribution).map(([os, count]) => (
        <Text key={os} component="p">{os}: {count} host(s)</Text>
      ))}

      <Text component="h3">Red Hat Products Detected</Text>
      {Object.entries(summary.products_found).map(([product, count]) => (
        <Text key={product} component="p">{product}: {count} instance(s)</Text>
      ))}

      <Button variant="primary" onClick={() => navigate(`/dashboard/${report.id}`)}>
        View Full Dashboard
      </Button>{" "}
      <Button variant="secondary" component="a" href={`/api/v1/reports/${report.id}/pdf/`}>
        Download PDF Report
      </Button>{" "}
      <Button variant="secondary" component="a" href={`/api/v1/reports/${report.id}/csv/`}>
        Export CSV
      </Button>{" "}
      <Button variant="link" onClick={onReset}>
        Run Another Health Check
      </Button>
    </TextContent>
  );
}
