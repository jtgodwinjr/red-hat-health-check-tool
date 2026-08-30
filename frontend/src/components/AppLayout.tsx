import { ReactNode } from "react";
import {
  Masthead,
  MastheadMain,
  MastheadBrand,
  PageSidebar,
  PageSidebarBody,
  Nav,
  NavList,
  NavItem,
} from "@patternfly/react-core";
import { useLocation, useNavigate } from "react-router-dom";

interface AppLayoutProps {
  children: ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
  const location = useLocation();
  const navigate = useNavigate();
  const isWizard = location.pathname === "/wizard";

  const sidebar = !isWizard ? (
    <PageSidebar>
      <PageSidebarBody>
        <Nav>
          <NavList>
            <NavItem isActive={location.pathname === "/wizard"} onClick={() => navigate("/wizard")}>
              New Health Check
            </NavItem>
            <NavItem isActive={location.pathname === "/credentials"} onClick={() => navigate("/credentials")}>
              Credentials
            </NavItem>
            <NavItem isActive={location.pathname === "/sources"} onClick={() => navigate("/sources")}>
              Sources
            </NavItem>
            <NavItem isActive={location.pathname === "/scans"} onClick={() => navigate("/scans")}>
              Scan History
            </NavItem>
            <NavItem isActive={location.pathname === "/reports"} onClick={() => navigate("/reports")}>
              Reports
            </NavItem>
          </NavList>
        </Nav>
      </PageSidebarBody>
    </PageSidebar>
  ) : undefined;

  return (
    <>
      <Masthead>
        <MastheadMain>
          <MastheadBrand>Red Hat Health Check</MastheadBrand>
        </MastheadMain>
      </Masthead>
      {sidebar}
      {children}
    </>
  );
}
