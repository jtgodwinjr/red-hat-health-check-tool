import { useEffect, useState } from "react";
import { PageSection, TextContent, Text, Label, Alert } from "@patternfly/react-core";
import { Table, Thead, Tr, Th, Tbody, Td } from "@patternfly/react-table";
import { apiClient } from "../api/client";

interface ScanListItem {
  id: number;
  status: string;
  scan_type: string;
  progress: { total_hosts: number; completed_hosts: number; found_systems: number };
  created_at: string;
  completed_at: string | null;
}

const statusColors: Record<string, "green" | "blue" | "red" | "orange" | "grey"> = {
  completed: "green",
  running: "blue",
  failed: "red",
  pending: "orange",
  cancelled: "grey",
};

export function ScansPage() {
  const [scans, setScans] = useState<ScanListItem[]>([]);

  useEffect(() => {
    apiClient.get<ScanListItem[]>("/scans/").then(setScans);
  }, []);

  return (
    <PageSection>
      <TextContent>
        <Text component="h1">Scan History</Text>
      </TextContent>
      <Table aria-label="Scans" variant="compact">
        <Thead><Tr><Th>ID</Th><Th>Type</Th><Th>Status</Th><Th>Hosts</Th><Th>Systems Found</Th><Th>Started</Th></Tr></Thead>
        <Tbody>
          {scans.map((s) => (
            <Tr key={s.id}>
              <Td>{s.id}</Td>
              <Td>{s.scan_type}</Td>
              <Td><Label color={statusColors[s.status] || "grey"}>{s.status}</Label></Td>
              <Td>{s.progress.completed_hosts}/{s.progress.total_hosts}</Td>
              <Td>{s.progress.found_systems}</Td>
              <Td>{new Date(s.created_at).toLocaleString()}</Td>
            </Tr>
          ))}
        </Tbody>
      </Table>
      {scans.length === 0 && <Alert variant="info" isInline title="No scans yet. Run a health check from the wizard." />}
    </PageSection>
  );
}
