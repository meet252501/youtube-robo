import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate } from "remotion";
import type { ProgressBarConfig } from "../lib/types";

interface ProgressBarProps {
  config?: ProgressBarConfig | null;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({ config }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  if (!config || config.enabled === false) {
    return null;
  }

  const {
    position = "top",
    height = 6,
    color = "#FFD700",
    backgroundColor = "rgba(0, 0, 0, 0.3)",
    glow = true,
  } = config;

  const progress = interpolate(frame, [0, durationInFrames - 1], [0, 100], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const isTop = position === "top";

  return (
    <div
      style={{
        position: "absolute",
        left: 0,
        right: 0,
        ...(isTop ? { top: 0 } : { bottom: 0 }),
        height: `${height}px`,
        backgroundColor,
        zIndex: 40,
        overflow: "hidden",
      }}
    >
      <div
        style={{
          width: `${progress}%`,
          height: "100%",
          backgroundColor: color,
          boxShadow: glow
            ? `0 0 12px ${color}, 0 0 4px rgba(255, 255, 255, 0.8)`
            : "none",
          transition: "width 0.05s linear",
          borderRadius: "0 2px 2px 0",
        }}
      />
    </div>
  );
};
