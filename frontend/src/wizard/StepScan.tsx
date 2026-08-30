import { useState, useEffect, useRef } from "react";
import {
  TextContent,
  Text,
  Button,
  Progress,
  Alert,
  FormGroup,
  FormSelect,
  FormSelectOption,
  DescriptionList,
  DescriptionListGroup,
  DescriptionListTerm,
  DescriptionListDescription,
} from "@patternfly/react-core";
import { apiClient } from "../api/client";
import { ScanStatus, WizardData } from "./types";

interface StepScanProps {
  data: WizardData;
  onUpdate: (data: Partial<WizardData>) => void;
}

export function StepScan({ data, onUpdate }: StepScanProps) {
  const [scanStatus, setScanStatus] = useState<ScanStatus | null>(null);
  const [scanType, setScanType] = useState<string>(data.scan_type);
  const [error, setError] = useState("");
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  const startScan = async () => {
    setError("");
    try {
      const scan = await apiClient.post<{ id: number; status: string }>("/scans/", {
        scan_type: scanType,
        source_ids: data.source_ids,
      });
      onUpdate({ scan_id: scan.id, scan_type: scanType as "quick" | "deep" });
      pollProgress(scan.id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to start scan");
    }
  };

  const pollProgress = (scanId: number) => {
    const poll = async () => {
      try {
        const status = await apiClient.get<ScanStatus>(`/scans/${scanId}/status/`);
        setScanStatus(status);
        if (status.status === "completed" || status.status === "failed" || status.status === "cancelled") {
          if (pollRef.current) clearInterval(pollRef.current);
        }
      } catch {
        // continue polling
      }
    };
    poll();
    pollRef.current = setInterval(poll, 2500);
  };

  const isRunning = scanStatus?.status === "running" || scanStatus?.status === "pending";
  const isComplete = scanStatus?.status === "completed";
  const isFailed = scanStatus?.status === "failed";
  const progress = scanStatus?.progress;

  return (
    <TextContent>
      <Text component="h2">Run Your Health Check</Text>

      {!scanStatus && (
        <>
          <DescriptionList>
            <DescriptionListGroup>
              <DescriptionListTerm>Sources to scan</DescriptionListTerm>
              <DescriptionListDescription>{data.source_ids.length} source(s) configured</DescriptionListDescription>
            </DescriptionListGroup>
            <DescriptionListGroup>
              <DescriptionListTerm>Credentials</DescriptionListTerm>
              <DescriptionListDescription>{data.credential_ids.length} credential(s) configured</DescriptionListDescription>
            </DescriptionListGroup>
          </DescriptionList>

          <FormGroup label="Scan depth" fieldId="scan-type">
            <FormSelect id="scan-type" value={scanType} onChange={(_e, v) => setScanType(v)}>
              <FormSelectOption value="quick" label="Quick Inventory — basic system info" />
              <FormSelectOption value="deep" label="Deep Inspection — products, subscriptions, packages" />
            </FormSelect>
          </FormGroup>

          <Button variant="primary" size="lg" onClick={startScan} isDisabled={data.source_ids.length === 0}>
            Start Health Check
          </Button>
        </>
      )}

      {error && <Alert variant="danger" isInline title={error} />}

      {isRunning && progress && (
        <>
          <Progress
            value={progress.total_hosts > 0 ? (progress.completed_hosts / progress.total_hosts) * 100 : 0}
            title="Scanning..."
            label={`${progress.completed_hosts} of ${progress.total_hosts} hosts`}
          />
          <Text component="p">
            Scanning {progress.current_source}... Found {progress.found_systems} system(s) so far.
          </Text>
        </>
      )}

      {isComplete && (
        <Alert variant="success" isInline title="Health check complete! Proceed to view your results." />
      )}

      {isFailed && (
        <>
          <Alert variant="danger" isInline title="Scan failed. You can retry or check your source configuration." />
          <Button variant="secondary" onClick={() => { setScanStatus(null); setError(""); }}>Retry</Button>
        </>
      )}
    </TextContent>
  );
}
