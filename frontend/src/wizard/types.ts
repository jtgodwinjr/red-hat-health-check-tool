export interface Credential {
  id: number;
  name: string;
  credential_type: "password" | "ssh_key" | "token";
  username: string;
  ssh_key_file: string;
  created_at: string;
  updated_at: string;
}

export interface Source {
  id: number;
  name: string;
  source_type: "ssh_network" | "openshift" | "satellite" | "ansible_aap" | "vcenter";
  hosts: string[];
  port: number;
  credential: number;
  created_at: string;
  updated_at: string;
}

export interface ConnectivityResult {
  host: string;
  status: "success" | "failed";
  message: string;
}

export interface ScanProgress {
  total_hosts: number;
  completed_hosts: number;
  found_systems: number;
  current_source: string;
}

export interface ScanStatus {
  id: number;
  status: "pending" | "running" | "completed" | "failed" | "cancelled";
  progress: ScanProgress;
  started_at: string | null;
  completed_at: string | null;
}

export interface WizardData {
  credential_ids: number[];
  source_ids: number[];
  scan_id: number | null;
  report_id: number | null;
  scan_type: "quick" | "deep";
}
