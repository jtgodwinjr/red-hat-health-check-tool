import { useState, useEffect } from "react";
import {
  TextContent,
  Text,
  Form,
  FormGroup,
  TextInput,
  FormSelect,
  FormSelectOption,
  ActionGroup,
  Button,
  Alert,
  DataList,
  DataListItem,
  DataListItemRow,
  DataListItemCells,
  DataListCell,
  DataListAction,
} from "@patternfly/react-core";
import { apiClient } from "../api/client";
import { Credential, WizardData } from "./types";

interface StepCredentialsProps {
  data: WizardData;
  onUpdate: (data: Partial<WizardData>) => void;
}

export function StepCredentials({ data, onUpdate }: StepCredentialsProps) {
  const [credentials, setCredentials] = useState<Credential[]>([]);
  const [name, setName] = useState("");
  const [credType, setCredType] = useState<string>("password");
  const [username, setUsername] = useState("");
  const [secret, setSecret] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    apiClient.get<Credential[]>("/credentials/").then(setCredentials);
  }, []);

  const handleAdd = async () => {
    setError("");
    setSuccess("");
    try {
      const cred = await apiClient.post<Credential>("/credentials/", {
        name,
        credential_type: credType,
        username,
        secret,
      });
      setCredentials([...credentials, cred]);
      onUpdate({ credential_ids: [...data.credential_ids, cred.id] });
      setName("");
      setUsername("");
      setSecret("");
      setSuccess(`Credential "${cred.name}" added.`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to add credential");
    }
  };

  const handleRemove = async (id: number) => {
    await apiClient.delete(`/credentials/${id}/`);
    setCredentials(credentials.filter((c) => c.id !== id));
    onUpdate({ credential_ids: data.credential_ids.filter((cid) => cid !== id) });
  };

  return (
    <TextContent>
      <Text component="h2">How do you connect to your systems?</Text>
      <Text component="p">Add the credentials needed to access your infrastructure.</Text>

      {error && <Alert variant="danger" isInline title={error} />}
      {success && <Alert variant="success" isInline title={success} />}

      {credentials.length > 0 && (
        <DataList aria-label="Credentials">
          {credentials.map((cred) => (
            <DataListItem key={cred.id}>
              <DataListItemRow>
                <DataListItemCells
                  dataListCells={[
                    <DataListCell key="name">{cred.name}</DataListCell>,
                    <DataListCell key="type">{cred.credential_type}</DataListCell>,
                    <DataListCell key="user">{cred.username}</DataListCell>,
                  ]}
                />
                <DataListAction id={`action-${cred.id}`} aria-label="Actions" aria-labelledby={`action-${cred.id}`}>
                  <Button variant="link" isDanger onClick={() => handleRemove(cred.id)}>Remove</Button>
                </DataListAction>
              </DataListItemRow>
            </DataListItem>
          ))}
        </DataList>
      )}

      <Form>
        <FormGroup label="Credential name" isRequired fieldId="cred-name">
          <TextInput id="cred-name" value={name} onChange={(_e, v) => setName(v)} placeholder="e.g., Production SSH" />
        </FormGroup>
        <FormGroup label="Type" isRequired fieldId="cred-type">
          <FormSelect id="cred-type" value={credType} onChange={(_e, v) => setCredType(v)}>
            <FormSelectOption value="password" label="Username & Password" />
            <FormSelectOption value="ssh_key" label="SSH Key" />
            <FormSelectOption value="token" label="Token" />
          </FormSelect>
        </FormGroup>
        {credType !== "token" && (
          <FormGroup label="Username" isRequired fieldId="cred-username">
            <TextInput id="cred-username" value={username} onChange={(_e, v) => setUsername(v)} placeholder="e.g., root" />
          </FormGroup>
        )}
        <FormGroup label={credType === "token" ? "Token" : "Password"} isRequired fieldId="cred-secret">
          <TextInput id="cred-secret" type="password" value={secret} onChange={(_e, v) => setSecret(v)} />
        </FormGroup>
        <ActionGroup>
          <Button variant="secondary" onClick={handleAdd} isDisabled={!name || !secret}>Add Credential</Button>
        </ActionGroup>
      </Form>
    </TextContent>
  );
}
