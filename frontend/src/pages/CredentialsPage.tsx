import { useEffect, useState } from "react";
import { PageSection, TextContent, Text, Button, Alert } from "@patternfly/react-core";
import { Table, Thead, Tr, Th, Tbody, Td } from "@patternfly/react-table";
import { apiClient } from "../api/client";
import { Credential } from "../wizard/types";

export function CredentialsPage() {
  const [credentials, setCredentials] = useState<Credential[]>([]);

  useEffect(() => {
    apiClient.get<Credential[]>("/credentials/").then(setCredentials);
  }, []);

  const handleDelete = async (id: number) => {
    await apiClient.delete(`/credentials/${id}/`);
    setCredentials(credentials.filter((c) => c.id !== id));
  };

  return (
    <PageSection>
      <TextContent>
        <Text component="h1">Credentials</Text>
        <Text component="p">Manage your saved connection credentials.</Text>
      </TextContent>
      <Table aria-label="Credentials" variant="compact">
        <Thead><Tr><Th>Name</Th><Th>Type</Th><Th>Username</Th><Th>Created</Th><Th>Actions</Th></Tr></Thead>
        <Tbody>
          {credentials.map((c) => (
            <Tr key={c.id}>
              <Td>{c.name}</Td>
              <Td>{c.credential_type}</Td>
              <Td>{c.username || "—"}</Td>
              <Td>{new Date(c.created_at).toLocaleDateString()}</Td>
              <Td><Button variant="link" isDanger onClick={() => handleDelete(c.id)}>Delete</Button></Td>
            </Tr>
          ))}
        </Tbody>
      </Table>
      {credentials.length === 0 && <Alert variant="info" isInline title="No credentials yet. Use the wizard to add some." />}
    </PageSection>
  );
}
