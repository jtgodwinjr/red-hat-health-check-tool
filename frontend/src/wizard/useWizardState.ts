import { useState, useEffect, useCallback } from "react";
import { apiClient } from "../api/client";
import { WizardData } from "./types";

interface WizardState {
  current_step: number;
  completed_steps: number[];
  data: WizardData;
}

const DEFAULT_DATA: WizardData = {
  credential_ids: [],
  source_ids: [],
  scan_id: null,
  report_id: null,
  scan_type: "quick",
};

export function useWizardState() {
  const [state, setState] = useState<WizardState>({
    current_step: 1,
    completed_steps: [],
    data: DEFAULT_DATA,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiClient
      .get<WizardState>("/wizard/state/")
      .then((s) => setState({ ...s, data: { ...DEFAULT_DATA, ...s.data } }))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const save = useCallback(
    async (updates: Partial<WizardState>) => {
      const newState = { ...state, ...updates };
      setState(newState);
      await apiClient.put("/wizard/state/", newState);
    },
    [state]
  );

  const goToStep = useCallback(
    (step: number) => {
      const completed = state.completed_steps.includes(state.current_step)
        ? state.completed_steps
        : [...state.completed_steps, state.current_step];
      save({ current_step: step, completed_steps: completed });
    },
    [state, save]
  );

  const updateData = useCallback(
    (data: Partial<WizardData>) => {
      save({ data: { ...state.data, ...data } });
    },
    [state, save]
  );

  const reset = useCallback(() => {
    save({ current_step: 1, completed_steps: [], data: DEFAULT_DATA });
  }, [save]);

  return { state, loading, goToStep, updateData, reset };
}
