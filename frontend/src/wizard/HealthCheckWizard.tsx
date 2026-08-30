import { Wizard, WizardStep } from "@patternfly/react-core";
import { useWizardState } from "./useWizardState";
import { StepWelcome } from "./StepWelcome";
import { StepCredentials } from "./StepCredentials";
import { StepSources } from "./StepSources";
import { StepScan } from "./StepScan";
import { StepResults } from "./StepResults";
import { Spinner } from "@patternfly/react-core";

export function HealthCheckWizard() {
  const { state, loading, goToStep, updateData, reset } = useWizardState();

  if (loading) return <Spinner size="xl" />;

  return (
    <Wizard
      height={600}
      title="Red Hat Health Check"
      startIndex={state.current_step}
      onStepChange={(_event, currentStep) => goToStep(currentStep.index ?? 1)}
    >
      <WizardStep name="Welcome" id="welcome">
        <StepWelcome />
      </WizardStep>
      <WizardStep name="Credentials" id="credentials">
        <StepCredentials data={state.data} onUpdate={updateData} />
      </WizardStep>
      <WizardStep name="Sources" id="sources" isDisabled={state.data.credential_ids.length === 0}>
        <StepSources data={state.data} onUpdate={updateData} />
      </WizardStep>
      <WizardStep name="Scan" id="scan" isDisabled={state.data.source_ids.length === 0}>
        <StepScan data={state.data} onUpdate={updateData} />
      </WizardStep>
      <WizardStep name="Results" id="results" isDisabled={!state.data.scan_id}>
        <StepResults data={state.data} onUpdate={updateData} onReset={reset} />
      </WizardStep>
    </Wizard>
  );
}
