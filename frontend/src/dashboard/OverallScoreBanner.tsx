import { ChartDonut } from "@patternfly/react-charts";

interface OverallScoreBannerProps {
  score: number;
  industryAverage: number;
}

export function OverallScoreBanner({ score, industryAverage }: OverallScoreBannerProps) {
  const diff = score - industryAverage;
  const assessment = score >= 80 ? "Excellent" : score >= 60 ? "Good" : score >= 40 ? "Needs Improvement" : "Critical";
  const donutColor = score >= 70 ? "#3E8635" : score >= 50 ? "#F0AB00" : "#C9190B";

  return (
    <div className="rh-overall-banner">
      <div style={{ display: "flex", alignItems: "center", gap: "2rem" }}>
        <div style={{ width: 160, height: 160 }}>
          <ChartDonut
            data={[
              { x: "Score", y: score },
              { x: "Remaining", y: 100 - score },
            ]}
            title={`${score}`}
            subTitle="Overall"
            colorScale={[donutColor, "#4F5255"]}
            innerRadius={55}
            width={160}
            height={160}
            padding={{ top: 0, bottom: 0, left: 0, right: 0 }}
          />
        </div>
        <div>
          <div className="rh-overall-label">{assessment}</div>
          <div style={{ fontSize: "0.875rem", color: "#D2D2D2", marginTop: "0.5rem" }}>
            Your environment health score across all categories
          </div>
        </div>
      </div>
      <div className="rh-avg-comparison">
        <div style={{ fontSize: "0.75rem", textTransform: "uppercase", letterSpacing: "0.05em" }}>Industry Average</div>
        <div className="avg-value">{industryAverage}</div>
        <div style={{ fontSize: "0.875rem", color: diff >= 0 ? "#3E8635" : "#C9190B" }}>
          {diff >= 0 ? `+${diff} above average` : `${Math.abs(diff)} below average`}
        </div>
      </div>
    </div>
  );
}
