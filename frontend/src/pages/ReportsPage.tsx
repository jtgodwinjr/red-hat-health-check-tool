import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { PageSection, TextContent, Text, Button, Alert } from "@patternfly/react-core";
import { Table, Thead, Tr, Th, Tbody, Td } from "@patternfly/react-table";
import { apiClient } from "../api/client";

interface ReportListItem {
  id: number;
  title: string;
  summary: { total_hosts: number; successful_hosts: number; failed_hosts: number };
  created_at: string;
}

export function ReportsPage() {
  const [reports, setReports] = useState<ReportListItem[]>([]);
  const navigate = useNavigate();

  useEffect(() => {
    apiClient.get<ReportListItem[]>("/reports/").then(setReports);
  }, []);

  return (
    <PageSection>
      <TextContent>
        <Text component="h1">Reports</Text>
      </TextContent>
      <Table aria-label="Reports" variant="compact">
        <Thead><Tr><Th>Title</Th><Th>Total Hosts</Th><Th>Successful</Th><Th>Failed</Th><Th>Date</Th><Th>Actions</Th></Tr></Thead>
        <Tbody>
          {reports.map((r) => (
            <Tr key={r.id}>
              <Td>{r.title}</Td>
              <Td>{r.summary.total_hosts}</Td>
              <Td>{r.summary.successful_hosts}</Td>
              <Td>{r.summary.failed_hosts}</Td>
              <Td>{new Date(r.created_at).toLocaleString()}</Td>
              <Td>
                <Button variant="link" onClick={() => navigate(`/dashboard/${r.id}`)}>View</Button>{" "}
                <Button variant="link" component="a" href={`/api/v1/reports/${r.id}/pdf/`}>PDF</Button>{" "}
                <Button variant="link" component="a" href={`/api/v1/reports/${r.id}/csv/`}>CSV</Button>
              </Td>
            </Tr>
          ))}
        </Tbody>
      </Table>
      {reports.length === 0 && <Alert variant="info" isInline title="No reports yet. Run a health check first." />}
    </PageSection>
  );
}
