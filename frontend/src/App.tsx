import { Routes, Route, Navigate } from "react-router-dom";
import { Page } from "@patternfly/react-core";
import { AppLayout } from "./components/AppLayout";
import { HealthCheckWizard } from "./wizard/HealthCheckWizard";

function App() {
  return (
    <Page>
      <AppLayout>
        <Routes>
          <Route path="/" element={<Navigate to="/wizard" replace />} />
          <Route path="/wizard" element={<HealthCheckWizard />} />
          <Route path="/dashboard/:reportId" element={<div>Dashboard placeholder</div>} />
          <Route path="/credentials" element={<div>Credentials placeholder</div>} />
          <Route path="/sources" element={<div>Sources placeholder</div>} />
          <Route path="/scans" element={<div>Scan history placeholder</div>} />
          <Route path="/reports" element={<div>Reports placeholder</div>} />
        </Routes>
      </AppLayout>
    </Page>
  );
}

export default App;
