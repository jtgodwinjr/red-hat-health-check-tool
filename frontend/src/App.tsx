import { Routes, Route, Navigate } from "react-router-dom";
import { Page } from "@patternfly/react-core";
import { AppLayout } from "./components/AppLayout";
import { HealthCheckWizard } from "./wizard/HealthCheckWizard";
import { Dashboard } from "./dashboard/Dashboard";
import { CredentialsPage } from "./pages/CredentialsPage";
import { SourcesPage } from "./pages/SourcesPage";
import { ScansPage } from "./pages/ScansPage";
import { ReportsPage } from "./pages/ReportsPage";

function App() {
  return (
    <Page>
      <AppLayout>
        <Routes>
          <Route path="/" element={<Navigate to="/wizard" replace />} />
          <Route path="/wizard" element={<HealthCheckWizard />} />
          <Route path="/dashboard/:reportId" element={<Dashboard />} />
          <Route path="/credentials" element={<CredentialsPage />} />
          <Route path="/sources" element={<SourcesPage />} />
          <Route path="/scans" element={<ScansPage />} />
          <Route path="/reports" element={<ReportsPage />} />
        </Routes>
      </AppLayout>
    </Page>
  );
}

export default App;
