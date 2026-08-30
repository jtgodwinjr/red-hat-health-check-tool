import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import {
  PageSection,
  TextContent,
  Text,
  Button,
  Toolbar,
  ToolbarContent,
  ToolbarItem,
  Spinner,
  Alert,
} from "@patternfly/react-core";
import { apiClient } from "../api/client";
import { SummaryCards } from "./SummaryCards";
import { OsDistributionChart } from "./OsDistributionChart";
import { ResultsTable } from "./ResultsTable";

interface ReportDetail {
  id: number;
  title: string;
  summary: {
    total_hosts: number;
    successful_hosts: number;
    failed_hosts: number;
    os_distribution: Record<string, number>;
    products_found: Record<string, number>;
  };
  results: Array<{
    id: number;
    host: string;
    status: "success" | "failed" | "skipped";
    data: Record<string, unknown>;
    error_message: string;
  }>;
  created_at: string;
}

export function Dashboard() {
  const { reportId } = useParams<{ reportId: string }>();
  const [report, setReport] = useState<ReportDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (reportId) {
      apiClient
        .get<ReportDetail>(`/reports/${reportId}/`)
        .then(setReport)
        .catch((e) => setError(e.message))
        .finally(() => setLoading(false));
    }
  }, [reportId]);

  if (loading) return <PageSection><Spinner size="xl" /></PageSection>;
  if (error) return <PageSection><Alert variant="danger" title={error} /></PageSection>;
  if (!report) return <PageSection><Alert variant="warning" title="Report not found" /></PageSection>;

  return (
    <PageSection>
      <TextContent>
        <Text component="h1">{report.title}</Text>
        <Text component="small">Generated {new Date(report.created_at).toLocaleString()}</Text>
      </TextContent>

      <Toolbar>
        <ToolbarContent>
          <ToolbarItem>
            <Button variant="primary" component="a" href={`/api/v1/reports/${report.id}/pdf/`}>Download PDF</Button>
          </ToolbarItem>
          <ToolbarItem>
            <Button variant="secondary" component="a" href={`/api/v1/reports/${report.id}/csv/`}>Export CSV</Button>
          </ToolbarItem>
        </ToolbarContent>
      </Toolbar>

      <SummaryCards
        totalHosts={report.summary.total_hosts}
        successfulHosts={report.summary.successful_hosts}
        failedHosts={report.summary.failed_hosts}
        productsFound={report.summary.products_found}
      />

      <OsDistributionChart
        distribution={report.summary.os_distribution}
        totalHosts={report.summary.successful_hosts}
      />

      <ResultsTable results={report.results as ReportDetail["results"]} />
    </PageSection>
  );
}
