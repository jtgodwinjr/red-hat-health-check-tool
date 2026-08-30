import { Card, CardBody, CardTitle, Icon } from "@patternfly/react-core";
import { CheckCircleIcon, TimesCircleIcon } from "@patternfly/react-icons";
import { ChartDonut } from "@patternfly/react-charts";

interface CheckDetail {
  label: string;
  passed: boolean;
  source: string;
  weight: number;
}

interface CategoryScoreCardProps {
  label: string;
  description: string;
  score: number;
  industryAverage: number;
  checks: Record<string, CheckDetail>;
}

export function CategoryScoreCard({ label, description, score, industryAverage, checks }: CategoryScoreCardProps) {
  const diff = score - industryAverage;
  const diffLabel = diff >= 0 ? `+${diff} above` : `${diff} below`;
  const diffColor = diff >= 0 ? "var(--rh-green)" : "var(--rh-red)";
  const donutColor = score >= industryAverage ? "#3E8635" : score >= industryAverage * 0.7 ? "#F0AB00" : "#C9190B";

  return (
    <Card>
      <CardTitle>{label}</CardTitle>
      <CardBody>
        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          <div style={{ width: 140, height: 140 }}>
            <ChartDonut
              data={[
                { x: "Score", y: score },
                { x: "Remaining", y: 100 - score },
              ]}
              title={`${score}`}
              subTitle="/ 100"
              colorScale={[donutColor, "#D2D2D2"]}
              innerRadius={45}
              constrainToVisibleArea
              width={140}
              height={140}
              padding={{ top: 0, bottom: 0, left: 0, right: 0 }}
            />
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: "0.875rem", color: "var(--rh-black-400)", marginBottom: "0.25rem" }}>{description}</div>
            <div style={{ fontSize: "0.875rem" }}>
              Industry avg: <strong>{industryAverage}</strong> |{" "}
              <span style={{ color: diffColor, fontWeight: 600 }}>{diffLabel}</span>
            </div>
          </div>
        </div>
        <ul className="rh-check-list">
          {Object.entries(checks).map(([key, check]) => (
            <li key={key}>
              {check.passed ? (
                <Icon status="success" size="sm"><CheckCircleIcon /></Icon>
              ) : (
                <Icon status="danger" size="sm"><TimesCircleIcon /></Icon>
              )}
              <span>{check.label}</span>
              <span style={{ marginLeft: "auto", fontSize: "0.75rem", color: "var(--rh-black-400)" }}>{check.source}</span>
            </li>
          ))}
        </ul>
      </CardBody>
    </Card>
  );
}
