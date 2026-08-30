import { useEffect, useState } from "react";
import { PageSection, TextContent, Text, Button, Alert } from "@patternfly/react-core";
import { Table, Thead, Tr, Th, Tbody, Td } from "@patternfly/react-table";
import { apiClient } from "../api/client";
import { Source } from "../wizard/types";

export function SourcesPage() {
  const [sources, setSources] = useState<Source[]>([]);

  useEffect(() => {
    apiClient.get<Source[]>("/sources/").then(setSources);
  }, []);

  const handleDelete = async (id: number) => {
    await apiClient.delete(`/sources/${id}/`);
    setSources(sources.filter((s) => s.id !== id));
  };

  return (
    <PageSection>
      <TextContent>
        <Text component="h1">Sources</Text>
        <Text component="p">Manage your scan targets.</Text>
      </TextContent>
      <Table aria-label="Sources" variant="compact">
        <Thead><Tr><Th>Name</Th><Th>Type</Th><Th>Hosts</Th><Th>Created</Th><Th>Actions</Th></Tr></Thead>
        <Tbody>
          {sources.map((s) => (
            <Tr key={s.id}>
              <Td>{s.name}</Td>
              <Td>{s.source_type}</Td>
              <Td>{s.hosts.length} host(s)</Td>
              <Td>{new Date(s.created_at).toLocaleDateString()}</Td>
              <Td><Button variant="link" isDanger onClick={() => handleDelete(s.id)}>Delete</Button></Td>
            </Tr>
          ))}
        </Tbody>
      </Table>
      {sources.length === 0 && <Alert variant="info" isInline title="No sources yet. Use the wizard to add some." />}
    </PageSection>
  );
}
