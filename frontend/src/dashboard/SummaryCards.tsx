import { Card, CardBody, Gallery, TextContent, Text } from "@patternfly/react-core";

interface SummaryCardsProps {
  totalHosts: number;
  successfulHosts: number;
  failedHosts: number;
  productsFound: Record<string, number>;
}

export function SummaryCards({ totalHosts, successfulHosts, failedHosts, productsFound }: SummaryCardsProps) {
  const totalProducts = Object.values(productsFound).reduce((a, b) => a + b, 0);

  return (
    <Gallery hasGutter minWidths={{ default: "180px" }}>
      <Card isCompact>
        <CardBody>
          <TextContent>
            <Text component="h2" style={{ fontSize: "2rem", margin: 0 }}>{totalHosts}</Text>
            <Text component="small">Total Hosts</Text>
          </TextContent>
        </CardBody>
      </Card>
      <Card isCompact>
        <CardBody>
          <TextContent>
            <Text component="h2" style={{ fontSize: "2rem", margin: 0, color: "var(--pf-t--global--color--status--success--default)" }}>{successfulHosts}</Text>
            <Text component="small">Successful</Text>
          </TextContent>
        </CardBody>
      </Card>
      <Card isCompact>
        <CardBody>
          <TextContent>
            <Text component="h2" style={{ fontSize: "2rem", margin: 0, color: "var(--pf-t--global--color--status--danger--default)" }}>{failedHosts}</Text>
            <Text component="small">Failed</Text>
          </TextContent>
        </CardBody>
      </Card>
      <Card isCompact>
        <CardBody>
          <TextContent>
            <Text component="h2" style={{ fontSize: "2rem", margin: 0 }}>{totalProducts}</Text>
            <Text component="small">Products Detected</Text>
          </TextContent>
        </CardBody>
      </Card>
    </Gallery>
  );
}
