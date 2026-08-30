import { Card, CardBody, CardTitle, Icon } from "@patternfly/react-core";
import { Table, Thead, Tr, Th, Tbody, Td } from "@patternfly/react-table";
import { CheckCircleIcon, ExclamationCircleIcon, MinusCircleIcon } from "@patternfly/react-icons";

interface ScanResult {
  id: number;
  host: string;
  status: "success" | "failed" | "skipped";
  data: {
    hostname?: string;
    os?: string;
    kernel?: string;
    arch?: string;
    cpu_count?: number;
    memory_mb?: number;
    products?: string[];
  };
  error_message: string;
}

interface ResultsTableProps {
  results: ScanResult[];
}

const statusIcons: Record<string, JSX.Element> = {
  success: <Icon status="success"><CheckCircleIcon /></Icon>,
  failed: <Icon status="danger"><ExclamationCircleIcon /></Icon>,
  skipped: <Icon status="warning"><MinusCircleIcon /></Icon>,
};

export function ResultsTable({ results }: ResultsTableProps) {
  return (
    <Card>
      <CardTitle>Scan Results</CardTitle>
      <CardBody>
        <Table aria-label="Scan results" variant="compact">
          <Thead>
            <Tr>
              <Th>Status</Th>
              <Th>Host</Th>
              <Th>Hostname</Th>
              <Th>OS</Th>
              <Th>Kernel</Th>
              <Th>CPUs</Th>
              <Th>Memory</Th>
              <Th>Products</Th>
              <Th>Error</Th>
            </Tr>
          </Thead>
          <Tbody>
            {results.map((r) => (
              <Tr key={r.id}>
                <Td>{statusIcons[r.status]}</Td>
                <Td>{r.host}</Td>
                <Td>{r.data.hostname || "—"}</Td>
                <Td>{r.data.os || "—"}</Td>
                <Td>{r.data.kernel || "—"}</Td>
                <Td>{r.data.cpu_count ?? "—"}</Td>
                <Td>{r.data.memory_mb ? `${Math.round(r.data.memory_mb / 1024)} GB` : "—"}</Td>
                <Td>{r.data.products?.join(", ") || "—"}</Td>
                <Td>{r.error_message || "—"}</Td>
              </Tr>
            ))}
          </Tbody>
        </Table>
      </CardBody>
    </Card>
  );
}
