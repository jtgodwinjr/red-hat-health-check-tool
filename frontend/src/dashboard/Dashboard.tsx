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
  Tab,
  Tabs,
  TabTitleText,
} from "@patternfly/react-core";
import { apiClient } from "../api/client";
import { OverallScoreBanner } from "./OverallScoreBanner";
import { CategoryScoreCard } from "./CategoryScoreCard";
import { SummaryCards } from "./SummaryCards";
import { OsDistributionChart } from "./OsDistributionChart";
import { ResultsTable } from "./ResultsTable";

interface CheckDetail {
  label: string;
  passed: boolean;
  source: string;
  weight: number;
}

interface CategoryScore {
  label: string;
  description: string;
  score: number;
  industry_average: number;
  checks: Record<string, CheckDetail>;
}

interface BenchmarkData {
  overall_score: number;
  overall_industry_average: number;
  categories: Record<string, CategoryScore>;
}

interface ReportDetail {
  id: number;
  title: string;
  summary: {
    total_hosts: number;
    successful_hosts: number;
    failed_hosts: number;
    os_distribution: Record<string, number>;
    products_found: Record<string, number>;
    benchmark?: BenchmarkData;
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
  const [activeTab, setActiveTab] = useState<string | number>(0);

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

  const benchmark = report.summary.benchmark;

  return (
    <>
      <PageSection variant="light">
        <TextContent>
          <Text component="h1">{report.title}</Text>
          <Text component="small">Generated {new Date(report.created_at).toLocaleString()}</Text>
        </TextContent>
        <Toolbar style={{ paddingLeft: 0 }}>
          <ToolbarContent>
            <ToolbarItem>
              <Button variant="primary" component="a" href={`/api/v1/reports/${report.id}/pdf/`}>Download PDF</Button>
            </ToolbarItem>
            <ToolbarItem>
              <Button variant="secondary" component="a" href={`/api/v1/reports/${report.id}/csv/`}>Export CSV</Button>
            </ToolbarItem>
          </ToolbarContent>
        </Toolbar>
      </PageSection>

      <PageSection>
        <Tabs activeKey={activeTab} onSelect={(_e, key) => setActiveTab(key)}>
          <Tab eventKey={0} title={<TabTitleText>Benchmark Analysis</TabTitleText>}>
            {benchmark ? (
              <>
                <div style={{ marginTop: "1.5rem" }}>
                  <OverallScoreBanner
                    score={benchmark.overall_score}
                    industryAverage={benchmark.overall_industry_average}
                  />
                </div>
                <div className="rh-category-grid">
                  {Object.entries(benchmark.categories).map(([key, cat]) => (
                    <CategoryScoreCard
                      key={key}
                      label={cat.label}
                      description={cat.description}
                      score={cat.score}
                      industryAverage={cat.industry_average}
                      checks={cat.checks}
                    />
                  ))}
                </div>
              </>
            ) : (
              <Alert variant="info" isInline title="No benchmark data available for this report." style={{ marginTop: "1rem" }} />
            )}
          </Tab>
          <Tab eventKey={1} title={<TabTitleText>Infrastructure Summary</TabTitleText>}>
            <div style={{ marginTop: "1.5rem" }}>
              <SummaryCards
                totalHosts={report.summary.total_hosts}
                successfulHosts={report.summary.successful_hosts}
                failedHosts={report.summary.failed_hosts}
                productsFound={report.summary.products_found}
              />
              <div style={{ marginTop: "1rem" }}>
                <OsDistributionChart
                  distribution={report.summary.os_distribution}
                  totalHosts={report.summary.successful_hosts}
                />
              </div>
            </div>
          </Tab>
          <Tab eventKey={2} title={<TabTitleText>Detailed Results</TabTitleText>}>
            <div style={{ marginTop: "1.5rem" }}>
              <ResultsTable results={report.results as ReportDetail["results"]} />
            </div>
          </Tab>
        </Tabs>
      </PageSection>
    </>
  );
}
