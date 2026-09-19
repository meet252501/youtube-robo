import React from "react";
import { useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import type { FocusBadgeConfig } from "../lib/types";

interface FocusBadgeProps {
  config?: FocusBadgeConfig | null;
}

const CATEGORY_ICONS: Record<string, string> = {
  insight: "💡",
  metric: "📈",
  principle: "⚡",
  alert: "⚠️",
  custom: "🎯",
};

export const FocusBadge: React.FC<FocusBadgeProps> = ({ config }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  if (!config || config.enabled === false || !config.text) {
    return null;
  }

  const {
    text,
    category = "insight",
    accentColor = "#00FF88",
    position = "top-center",
    startMs = 0,
    durationMs = 6000,
  } = config;

  const currentTimeMs = (frame / fps) * 1000;
  const endMs = startMs + durationMs;

  if (currentTimeMs < startMs || currentTimeMs > endMs) {
    return null;
  }

  const startFrame = Math.round((startMs / 1000) * fps);
  const durationFrames = Math.round((durationMs / 1000) * fps);
  const elapsed = frame - startFrame;
  const remaining = durationFrames - elapsed;

  // Spring entrance from top
  const enterSpring = spring({
    frame: elapsed,
    fps,
    config: { damping: 14, stiffness: 180 },
  });

  // Smooth exit fade
  const exitOpacity = interpolate(
    remaining,
    [0, Math.min(15, durationFrames / 2)],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  const opacity = Math.min(enterSpring, exitOpacity);
  const translateY = interpolate(enterSpring, [0, 1], [-25, 0]);

  const positionStyle: React.CSSProperties =
    position === "top-center"
      ? { top: "13%", left: "50%", transform: `translateX(-50%) translateY(${translateY}px)` }
      : position === "top-left"
      ? { top: "13%", left: "8%", transform: `translateY(${translateY}px)` }
      : { top: "13%", right: "8%", transform: `translateY(${translateY}px)` };

  const icon = CATEGORY_ICONS[category] || "🎯";

  return (
    <div
      style={{
        position: "absolute",
        ...positionStyle,
        opacity,
        zIndex: 42,
        pointerEvents: "none",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "10px",
          background: "rgba(16, 16, 24, 0.78)",
          backdropFilter: "blur(18px)",
          WebkitBackdropFilter: "blur(18px)",
          border: `1.5px solid ${accentColor}55`,
          boxShadow: `0 8px 28px rgba(0, 0, 0, 0.65), 0 0 16px ${accentColor}33`,
          borderRadius: "999px",
          padding: "8px 20px",
        }}
      >
        {/* Glowing Pulsing Status Dot / Icon */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: "16px",
          }}
        >
          {icon}
        </div>

        {/* Text */}
        <span
          style={{
            fontFamily: "Montserrat, -apple-system, sans-serif",
            fontSize: "20px",
            fontWeight: 800,
            textTransform: "uppercase",
            letterSpacing: "0.08em",
            color: "#FFFFFF",
            textShadow: "0 2px 8px rgba(0,0,0,0.8)",
          }}
        >
          {text}
        </span>
      </div>
    </div>
  );
};
