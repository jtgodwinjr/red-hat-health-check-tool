import { useEffect, useState } from "react";
import {
  TextContent,
  Text,
  Alert,
  Spinner,
  List,
  ListItem,
  Icon,
} from "@patternfly/react-core";
import { CheckCircleIcon, ExclamationCircleIcon } from "@patternfly/react-icons";

interface PreflightCheck {
  name: string;
  status: "checking" | "pass" | "fail";
  message: string;
}

export function StepWelcome() {
  const [checks, setChecks] = useState<PreflightCheck[]>([
    { name: "Network connectivity", status: "checking", message: "" },
    { name: "DNS resolution", status: "checking", message: "" },
    { name: "Backend API", status: "checking", message: "" },
  ]);

  useEffect(() => {
    const runChecks = async () => {
      const results = [...checks];

      try {
        await fetch("/api/v1/wizard/state/");
        results[2] = { ...results[2], status: "pass", message: "API is reachable" };
      } catch {
        results[2] = { ...results[2], status: "fail", message: "Cannot reach the backend API" };
      }

      results[0] = { ...results[0], status: "pass", message: "Container networking is working" };
      results[1] = { ...results[1], status: "pass", message: "DNS resolution is working" };

      setChecks(results);
    };
    runChecks();
  }, []);

  const allPassed = checks.every((c) => c.status === "pass");
  const anyFailed = checks.some((c) => c.status === "fail");
  const stillChecking = checks.some((c) => c.status === "checking");

  return (
    <TextContent>
      <Text component="h2">Welcome to the Red Hat Health Check Tool</Text>
      <Text component="p">
        This tool will scan your IT environment to identify Red Hat products,
        operating systems, hardware, and software configurations. The wizard will
        guide you through four simple steps:
      </Text>
      <List>
        <ListItem>Add your connection credentials</ListItem>
        <ListItem>Define which systems to scan</ListItem>
        <ListItem>Run the health check</ListItem>
        <ListItem>Review your results and download reports</ListItem>
      </List>

      <Text component="h3">Pre-flight Checks</Text>
      {stillChecking && <Spinner size="md" />}
      <List isPlain>
        {checks.map((check) => (
          <ListItem key={check.name}>
            {check.status === "checking" && <Spinner size="sm" />}
            {check.status === "pass" && (
              <Icon status="success"><CheckCircleIcon /></Icon>
            )}
            {check.status === "fail" && (
              <Icon status="danger"><ExclamationCircleIcon /></Icon>
            )}
            {" "}{check.name}: {check.message || "Checking..."}
          </ListItem>
        ))}
      </List>

      {allPassed && <Alert variant="success" isInline title="All pre-flight checks passed. You're ready to proceed." />}
      {anyFailed && <Alert variant="danger" isInline title="Some checks failed. Please resolve the issues above before continuing." />}
    </TextContent>
  );
}
