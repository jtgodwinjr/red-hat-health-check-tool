# Red Hat Health Check Tool — Design Spec

## Overview

A streamlined, customer-facing health check tool for Red Hat environments. Based on the quipucords project's scanning capabilities, repackaged into a single-container application with a guided wizard UI. Designed for customer self-service — no Red Hat staff involvement required.

## Goals

1. **Simplify deployment** — one container, one command to start (`podman run -p 8080:8080 redhat-healthcheck`)
2. **Guide the user** — a 5-step wizard replaces the "read the docs" onboarding of quipucords
3. **Validate early** — pre-flight connectivity checks catch problems before scanning, not during
4. **Deliver actionable results** — interactive dashboard, PDF reports, CSV exports
5. **Full scan coverage** — support all 5 quipucords source types from day one

## Target User

End customers running their own infrastructure health checks with minimal Red Hat involvement. They may not be deeply technical. The UI must explain what each step does in plain language and catch errors before they become silent failures.

## Architecture

### Monorepo Structure

```
redhat-healthcheck/
├── backend/                  # Django project
│   ├── healthcheck/          # Django settings, urls, wsgi
│   ├── credentials/          # Credential management app
│   ├── sources/              # Source definition app
│   ├── scans/                # Scan orchestration app
│   ├── reports/              # Report generation app
│   ├── wizard/               # Wizard state/progress tracking API
│   └── scanner/              # Forked quipucords scanning logic
├── frontend/                 # React + PatternFly
│   ├── src/
│   │   ├── components/       # Shared UI components
│   │   ├── wizard/           # Setup wizard flow
│   │   ├── dashboard/        # Health check dashboard & reports
│   │   └── pages/            # Credentials, sources, scans, history
│   └── package.json
├── Dockerfile                # Single container build
├── docker-compose.yml        # Dev environment
└── manage.py
```

### Tech Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Backend | Python 3.12, Django | Maximizes code reuse from quipucords |
| Task Queue | Huey (SQLite broker) | Replaces Celery + Redis — zero external dependencies |
| Database | SQLite | Embedded, zero-config, sufficient for single-user health checks |
| Frontend | React, TypeScript, PatternFly | Red Hat design system with built-in wizard component |
| Static Files | WhiteNoise | Django serves the React build directly — no nginx |
| Container | Podman/Docker | Single container, single process + Huey consumer thread |
| PDF Export | WeasyPrint or ReportLab | Server-side PDF generation |

### Key Simplifications from Quipucords

- SQLite replaces PostgreSQL — no database server to manage
- Huey replaces Celery + Redis — lightweight, embedded task queue
- Django serves the React build via WhiteNoise — no separate frontend server
- Single repo replaces three (backend, UI, CLI)
- CLI is eliminated — wizard UI covers all setup and operation

## Wizard UI Flow

The wizard is the primary user interface. Built with PatternFly's `Wizard` component.

### Step 1: Welcome & Pre-flight Check

- Brief explanation of what the tool does and what to expect
- Automatic pre-flight checks: container networking, DNS resolution, outbound connectivity
- Plain-language results with actionable guidance if issues are found

### Step 2: Add Credentials

- Plain-language prompt: "How do you connect to your systems?"
- Guided forms per credential type: SSH key upload, username/password, token-based auth
- Inline format validation before proceeding
- Support for multiple credentials (e.g., one for Linux hosts, one for OpenShift)

### Step 3: Define Sources

- Plain-language prompt: "What do you want to scan?"
- Source type selection with icons and descriptions
- Per-type guided forms:
  - **SSH Network:** IP range or hostname list with "Test Connection" button
  - **OpenShift:** Cluster URL + token with live connection test
  - **Satellite:** Server URL + credentials, validated on entry
  - **Ansible AAP:** Server URL + credentials, validated on entry
  - **VMware vCenter:** Server URL + credentials, validated on entry
- Pre-flight check per source: validates connectivity and credentials before proceeding
- Actionable error messages on failure (e.g., "Host 10.0.1.5: Connection refused — is SSH running on port 22?")

### Step 4: Configure & Run Scan

- Summary of sources and credential mappings
- Optional scan depth selection (quick inventory vs. deep inspection)
- "Start Health Check" button with real-time progress
- Per-source status updates: "Scanning 12/50 hosts... Found 8 RHEL systems so far"

### Step 5: Results & Reports

- Wizard completes into the interactive dashboard
- Summary cards: total systems, RHEL versions, product subscriptions, compliance status
- Prominent "Download PDF Report" and "Export CSV" buttons
- "Run Another Health Check" and "Modify Sources & Rescan" options

### Post-Wizard Experience

After the first run, users land on the dashboard directly. A "New Health Check" button re-enters the wizard. Sidebar navigation provides direct access to:
- Credentials management
- Sources management
- Scan history
- Past reports

## API Design

```
/api/v1/
├── credentials/              # CRUD
├── sources/                  # CRUD
│   └── {id}/test/            # POST — pre-flight connectivity check
├── scans/                    # Create, list, cancel
│   └── {id}/status/          # GET — real-time scan progress
├── reports/                  # List past reports
│   └── {id}/                 # GET — dashboard JSON data
│   └── {id}/pdf/             # GET — download PDF
│   └── {id}/csv/             # GET — download CSV
└── wizard/
    └── state/                # GET/PUT — wizard progress tracking
```

## Scan Execution Flow

1. User clicks "Start Health Check" in wizard step 4
2. Frontend POSTs to `/api/v1/scans/` with source + credential mappings
3. Django creates a Scan record and enqueues a Huey task
4. Huey worker runs the forked quipucords scanner logic
5. Scanner updates the Scan record's progress as it processes hosts
6. Frontend polls `/api/v1/scans/{id}/status/` every 2-3 seconds
7. On completion, scanner generates a Report record with structured results
8. Frontend redirects to the dashboard view of the report

## Error Handling

### Philosophy

Surface problems early with plain-language explanations. No silent failures.

### Pre-flight Errors (Wizard Steps 1-3)

- Connection failures show specific host, port, and what to check
- Credential failures distinguish between: auth rejected, host unreachable, permission denied
- Users fix and re-test without leaving the current wizard step

### Scan Errors (Step 4)

- Per-host status tracking: success, failed, or skipped
- Partial success is valid — report includes what was scanned and lists failures with reasons
- Configurable scan timeout with sensible default (30 seconds per host)
- If Huey worker dies mid-scan, scan is marked "failed" on next startup with a "Retry" option

### API Error Format

```json
{
  "error": "human_readable_message",
  "code": "MACHINE_CODE",
  "detail": {}
}
```

- Toast notifications for transient errors
- Inline messages for form validation
- Unhandled exceptions logged to container stdout (12-factor style)

## Security

- **Credential encryption:** Fernet symmetric encryption at rest. Key generated on first run, persisted to a mounted volume
- **No default passwords:** First-run generates a random admin token displayed in container logs
- **HTTPS:** App runs HTTP inside container. Documentation guides TLS termination via reverse proxy. Self-signed cert generation available as convenience option
- **Network scoping:** Scanner only reaches hosts explicitly defined as sources — no network autodiscovery
- **Session management:** Django session auth with configurable timeout (default 8 hours)
- **No data exfiltration:** All results stored locally, no telemetry, no phone-home

## Testing Strategy

### Backend

- **Unit tests** (pytest + Django test framework) per app: credentials, sources, scans, reports, wizard
- **Scanner tests** with mocked SSH/API connections
- **API tests** via Django REST framework test client
- **Integration test:** end-to-end credentials → source → scan → report against a mock SSH target container

### Frontend

- **Component tests** (Jest + React Testing Library) for wizard steps, dashboard, forms
- **Wizard flow test** for full step 1-5 progression including navigation and validation gates
- **Accessibility** testing for wizard keyboard navigation and screen reader compatibility

### Infrastructure

- Dockerfile builds and starts cleanly
- App accessible on expected port after container start
- SQLite database created on first run
- Encryption key generated and persisted to volume

### Out of Scope

- No load testing or multi-user stress tests (single-user tool)
- No browser-based E2E (Cypress/Playwright) at launch — wizard testable at component level
