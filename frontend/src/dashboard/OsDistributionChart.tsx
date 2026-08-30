import { Card, CardBody, CardTitle, DescriptionList, DescriptionListGroup, DescriptionListTerm, DescriptionListDescription, Progress } from "@patternfly/react-core";

interface OsDistributionChartProps {
  distribution: Record<string, number>;
  totalHosts: number;
}

export function OsDistributionChart({ distribution, totalHosts }: OsDistributionChartProps) {
  const sorted = Object.entries(distribution).sort(([, a], [, b]) => b - a);

  return (
    <Card>
      <CardTitle>Operating System Distribution</CardTitle>
      <CardBody>
        <DescriptionList>
          {sorted.map(([os, count]) => (
            <DescriptionListGroup key={os}>
              <DescriptionListTerm>{os}</DescriptionListTerm>
              <DescriptionListDescription>
                <Progress
                  value={totalHosts > 0 ? (count / totalHosts) * 100 : 0}
                  label={`${count} host(s)`}
                  measureLocation="outside"
                />
              </DescriptionListDescription>
            </DescriptionListGroup>
          ))}
        </DescriptionList>
      </CardBody>
    </Card>
  );
}
