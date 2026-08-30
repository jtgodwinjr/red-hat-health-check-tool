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
  TextContent,
  Text,
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
          <MastheadBrand>
            <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
              <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
                <rect width="36" height="36" rx="4" fill="#EE0000"/>
                <path d="M8 18L14 24L28 10" stroke="white" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              <TextContent>
                <Text component="h4" style={{ color: "white", margin: 0, fontWeight: 600 }}>
                  Red Hat Health Check
                </Text>
              </TextContent>
            </div>
          </MastheadBrand>
        </MastheadMain>
      </Masthead>
      {sidebar}
      {children}
    </>
  );
}
