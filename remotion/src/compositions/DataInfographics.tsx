import React from "react";
import { AbsoluteFill, spring, useCurrentFrame, useVideoConfig } from "remotion";

export interface DataVisualizationConfig {
  hasMetrics: boolean;
  metricValue: string;
  metricLabel: string;
  chartType: string;
  timestampStart: number;
}

interface DataInfographicsProps {
  config?: DataVisualizationConfig;
}

export const DataInfographics: React.FC<DataInfographicsProps> = ({ config }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  if (!config || !config.hasMetrics || config.chartType === "none") {
    return null;
  }

  // Calculate start frame
  const startFrame = Math.round(config.timestampStart * fps);
  if (frame < startFrame) {
    return null;
  }

  const progress = spring({
    frame: frame - startFrame,
    fps,
    config: { mass: 1, damping: 12, stiffness: 100 },
  });

  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
        pointerEvents: "none",
      }}
    >
      <div
        style={{
          transform: `scale(${progress}) translateY(${
            (1 - progress) * 50
          }px)`,
          opacity: progress,
          backgroundColor: "rgba(0, 0, 0, 0.75)",
          backdropFilter: "blur(10px)",
          border: "1px solid rgba(255, 255, 255, 0.2)",
          borderRadius: "24px",
          padding: "32px 48px",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          boxShadow: "0 20px 40px rgba(0,0,0,0.5)",
          marginTop: "-150px", // Push it above the center
        }}
      >
        <span
          style={{
            fontSize: "120px",
            fontWeight: 900,
            fontFamily: "Inter, sans-serif",
            color: "#00FF88",
            textShadow: "0 0 20px rgba(0, 255, 136, 0.4)",
            lineHeight: 1,
            letterSpacing: "-0.04em",
          }}
        >
          {config.metricValue}
        </span>
        <span
          style={{
            fontSize: "40px",
            fontWeight: 600,
            fontFamily: "Inter, sans-serif",
            color: "#FFFFFF",
            opacity: 0.9,
            marginTop: "16px",
            letterSpacing: "-0.01em",
          }}
        >
          {config.metricLabel}
        </span>
      </div>
    </AbsoluteFill>
  );
};
