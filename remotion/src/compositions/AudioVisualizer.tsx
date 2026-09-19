import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate } from "remotion";
import type { AudioVisualizerConfig } from "../lib/types";

interface AudioVisualizerProps {
  config?: AudioVisualizerConfig | null;
}

export const AudioVisualizer: React.FC<AudioVisualizerProps> = ({ config }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  if (!config || config.enabled === false) {
    return null;
  }

  const {
    barCount = 18,
    color = "#FFD700",
    position = "bottom-center",
    height = 40,
    width = 240,
  } = config;

  const positionStyle: React.CSSProperties =
    position === "bottom-center"
      ? { bottom: "6%", left: "50%", transform: "translateX(-50%)" }
      : position === "bottom-left"
      ? { bottom: "6%", left: "8%" }
      : { bottom: "6%", right: "8%" };

  // Generate dynamic wave patterns based on frame rhythm
  const bars = Array.from({ length: barCount }, (_, i) => {
    // Harmonic frequencies simulating voice rhythm
    const freq1 = Math.sin(frame * 0.25 + i * 0.4);
    const freq2 = Math.cos(frame * 0.15 - i * 0.3);
    const freq3 = Math.sin(frame * 0.4 + i * 0.6);
    
    const combined = Math.abs((freq1 + freq2 + freq3) / 3);
    const barHeight = Math.max(4, combined * height);

    return barHeight;
  });

  return (
    <div
      style={{
        position: "absolute",
        ...positionStyle,
        width: `${width}px`,
        height: `${height}px`,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        gap: "4px",
        zIndex: 35,
        pointerEvents: "none",
        background: "rgba(0, 0, 0, 0.25)",
        padding: "6px 14px",
        borderRadius: "20px",
        backdropFilter: "blur(6px)",
      }}
    >
      {bars.map((h, i) => (
        <div
          key={i}
          style={{
            flex: 1,
            height: `${h}px`,
            backgroundColor: color,
            borderRadius: "4px",
            boxShadow: `0 0 8px ${color}88`,
            transition: "height 0.08s ease-out",
          }}
        />
      ))}
    </div>
  );
};
