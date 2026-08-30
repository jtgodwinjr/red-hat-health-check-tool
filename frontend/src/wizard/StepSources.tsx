import { useState, useEffect } from "react";
import {
  TextContent,
  Text,
  Form,
  FormGroup,
  TextInput,
  TextArea,
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
  List,
  ListItem,
  Icon,
} from "@patternfly/react-core";
import { CheckCircleIcon, ExclamationCircleIcon } from "@patternfly/react-icons";
import { apiClient } from "../api/client";
import { Source, Credential, ConnectivityResult, WizardData } from "./types";

interface StepSourcesProps {
  data: WizardData;
  onUpdate: (data: Partial<WizardData>) => void;
}

const SOURCE_LABELS: Record<string, string> = {
  ssh_network: "SSH Network",
  openshift: "OpenShift",
  satellite: "Red Hat Satellite",
  ansible_aap: "Ansible Automation Platform",
  vcenter: "VMware vCenter",
};

const SOURCE_DESCRIPTIONS: Record<string, string> = {
  ssh_network: "Scan Linux hosts over SSH. Enter IP addresses or hostnames, one per line.",
  openshift: "Scan an OpenShift cluster via its API.",
  satellite: "Scan systems managed by Red Hat Satellite.",
  ansible_aap: "Scan Ansible Automation Platform.",
  vcenter: "Scan VMware vCenter for virtual machines.",
};

export function StepSources({ data, onUpdate }: StepSourcesProps) {
  const [sources, setSources] = useState<Source[]>([]);
  const [credentials, setCredentials] = useState<Credential[]>([]);
  const [name, setName] = useState("");
  const [sourceType, setSourceType] = useState("ssh_network");
  const [hostsRaw, setHostsRaw] = useState("");
  const [port, setPort] = useState("22");
  const [credentialId, setCredentialId] = useState<string>("");
  const [error, setError] = useState("");
  const [testing, setTesting] = useState<number | null>(null);
  const [testResults, setTestResults] = useState<Record<number, ConnectivityResult[]>>({});

  useEffect(() => {
    apiClient.get<Source[]>("/sources/").then(setSources);
    apiClient.get<Credential[]>("/credentials/").then((creds) => {
      setCredentials(creds);
      if (creds.length > 0) setCredentialId(String(creds[0].id));
    });
  }, []);

  const handleAdd = async () => {
    setError("");
    const hosts = hostsRaw.split("\n").map((h) => h.trim()).filter(Boolean);
    if (hosts.length === 0) {
      setError("Please enter at least one host.");
      return;
    }
    try {
      const source = await apiClient.post<Source>("/sources/", {
        name,
        source_type: sourceType,
        hosts,
        port: parseInt(port, 10),
        credential: parseInt(credentialId, 10),
      });
      setSources([...sources, source]);
      onUpdate({ source_ids: [...data.source_ids, source.id] });
      setName("");
      setHostsRaw("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to add source");
    }
  };

  const handleTest = async (sourceId: number) => {
    setTesting(sourceId);
    try {
      const resp = await apiClient.post<{ results: ConnectivityResult[] }>(`/sources/${sourceId}/test/`, {});
      setTestResults({ ...testResults, [sourceId]: resp.results });
    } catch {
      setTestResults({ ...testResults, [sourceId]: [{ host: "unknown", status: "failed", message: "Test failed" }] });
    }
    setTesting(null);
  };

  const handleRemove = async (id: number) => {
    await apiClient.delete(`/sources/${id}/`);
    setSources(sources.filter((s) => s.id !== id));
    onUpdate({ source_ids: data.source_ids.filter((sid) => sid !== id) });
  };

  return (
    <TextContent>
      <Text component="h2">What do you want to scan?</Text>

      {error && <Alert variant="danger" isInline title={error} />}

      {sources.length > 0 && (
        <DataList aria-label="Sources">
          {sources.map((source) => (
            <DataListItem key={source.id}>
              <DataListItemRow>
                <DataListItemCells
                  dataListCells={[
                    <DataListCell key="name">{source.name}</DataListCell>,
                    <DataListCell key="type">{SOURCE_LABELS[source.source_type]}</DataListCell>,
                    <DataListCell key="hosts">{source.hosts.length} host(s)</DataListCell>,
                  ]}
                />
                <DataListAction id={`action-${source.id}`} aria-label="Actions" aria-labelledby={`action-${source.id}`}>
                  <Button variant="secondary" onClick={() => handleTest(source.id)} isLoading={testing === source.id} isDisabled={testing !== null}>
                    Test Connection
                  </Button>
                  <Button variant="link" isDanger onClick={() => handleRemove(source.id)}>Remove</Button>
                </DataListAction>
              </DataListItemRow>
              {testResults[source.id] && (
                <List isPlain>
                  {testResults[source.id].map((r, i) => (
                    <ListItem key={i}>
                      {r.status === "success" ? (
                        <Icon status="success"><CheckCircleIcon /></Icon>
                      ) : (
                        <Icon status="danger"><ExclamationCircleIcon /></Icon>
                      )}
                      {" "}{r.host}: {r.message}
                    </ListItem>
                  ))}
                </List>
              )}
            </DataListItem>
          ))}
        </DataList>
      )}

      <Form>
        <FormGroup label="Source name" isRequired fieldId="src-name">
          <TextInput id="src-name" value={name} onChange={(_e, v) => setName(v)} placeholder="e.g., Production Servers" />
        </FormGroup>
        <FormGroup label="Source type" isRequired fieldId="src-type">
          <FormSelect id="src-type" value={sourceType} onChange={(_e, v) => setSourceType(v)}>
            {Object.entries(SOURCE_LABELS).map(([value, label]) => (
              <FormSelectOption key={value} value={value} label={label} />
            ))}
          </FormSelect>
        </FormGroup>
        <Text component="small">{SOURCE_DESCRIPTIONS[sourceType]}</Text>
        <FormGroup label={sourceType === "ssh_network" ? "Hosts (one per line)" : "URL"} isRequired fieldId="src-hosts">
          <TextArea id="src-hosts" value={hostsRaw} onChange={(_e, v) => setHostsRaw(v)} placeholder={sourceType === "ssh_network" ? "10.0.1.1\n10.0.1.2\nserver.example.com" : "https://api.example.com"} rows={4} />
        </FormGroup>
        <FormGroup label="Port" fieldId="src-port">
          <TextInput id="src-port" type="number" value={port} onChange={(_e, v) => setPort(v)} />
        </FormGroup>
        <FormGroup label="Credential" isRequired fieldId="src-cred">
          <FormSelect id="src-cred" value={credentialId} onChange={(_e, v) => setCredentialId(v)}>
            {credentials.map((c) => (
              <FormSelectOption key={c.id} value={String(c.id)} label={`${c.name} (${c.credential_type})`} />
            ))}
          </FormSelect>
        </FormGroup>
        <ActionGroup>
          <Button variant="secondary" onClick={handleAdd} isDisabled={!name || !hostsRaw || !credentialId}>Add Source</Button>
        </ActionGroup>
      </Form>
    </TextContent>
  );
}
