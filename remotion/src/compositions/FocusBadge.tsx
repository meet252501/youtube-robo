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
    cardPosition = "center",
    startMs = 0,
    durationMs = 6000,
    variant = "badge",
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

  const icon = CATEGORY_ICONS[category] || "🎯";

  // ── VARIANT: CARD ── Takeaway card with face-safe cardPosition support ──
  if (variant === "card") {
    const cardScale = interpolate(enterSpring, [0, 1], [0.85, 1]);

    let cardContainerStyle: React.CSSProperties;
    let cardAlignItems: "flex-start" | "flex-end" | "center" = "center";
    let cardTextAlign: "left" | "right" | "center" = "center";

    switch (cardPosition) {
      case "center-left":
        cardContainerStyle = {
          top: "43.5%",
          left: "7%",
          width: "43%",
          transform: `translateY(${translateY}px) scale(${cardScale})`,
        };
        cardAlignItems = "flex-start";
        cardTextAlign = "left";
        break;
      case "center-right":
        cardContainerStyle = {
          top: "42%",
          right: "7%",
          width: "44%",
          transform: `translateY(${translateY}px) scale(${cardScale})`,
        };
        cardAlignItems = "flex-end";
        cardTextAlign = "right";
        break;
      case "lower-left":
        cardContainerStyle = {
          top: "56%",
          left: "7%",
          width: "44%",
          transform: `translateY(${translateY}px) scale(${cardScale})`,
        };
        cardAlignItems = "flex-start";
        cardTextAlign = "left";
        break;
      case "lower-right":
        cardContainerStyle = {
          top: "56%",
          right: "7%",
          width: "44%",
          transform: `translateY(${translateY}px) scale(${cardScale})`,
        };
        cardAlignItems = "flex-end";
        cardTextAlign = "right";
        break;
      case "center":
      default:
        cardContainerStyle = {
          top: "38%",
          left: "50%",
          transform: `translateX(-50%) translateY(${translateY}px) scale(${cardScale})`,
          maxWidth: "85%",
        };
        break;
    }

    const isSideCard =
      cardPosition === "center-left" ||
      cardPosition === "center-right" ||
      cardPosition === "lower-left" ||
      cardPosition === "lower-right";

    return (
      <div
        style={{
          position: "absolute",
          ...cardContainerStyle,
          opacity,
          zIndex: 50,
          pointerEvents: "none",
        }}
      >
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: cardAlignItems,
            justifyContent: "center",
            gap: "8px",
            background: "rgba(10, 10, 16, 0.90)",
            backdropFilter: "blur(24px)",
            WebkitBackdropFilter: "blur(24px)",
            border: `2px solid ${accentColor}66`,
            boxShadow: `0 12px 48px rgba(0, 0, 0, 0.7), 0 0 24px ${accentColor}22`,
            borderRadius: "18px",
            padding: isSideCard ? "22px 24px" : "28px 48px",
            width: isSideCard ? "100%" : undefined,
            minWidth: isSideCard ? undefined : "420px",
            boxSizing: "border-box",
          }}
        >
          <span
            style={{
              fontSize: "22px",
              marginBottom: "2px",
            }}
          >
            {icon}
          </span>
          <span
            style={{
              fontFamily: "Montserrat, -apple-system, sans-serif",
              fontSize: isSideCard ? "28px" : "38px",
              fontWeight: 900,
              textTransform: "uppercase",
              letterSpacing: "0.06em",
              color: "#FFFFFF",
              textShadow: "0 3px 12px rgba(0,0,0,0.9)",
              textAlign: cardTextAlign,
              lineHeight: 1.25,
              whiteSpace: "pre-line",
              wordBreak: "break-word",
            }}
          >
            {text}
          </span>
        </div>
      </div>
    );
  }

  // ── VARIANT: BADGE (default) ── Small pill label ──
  const positionStyle: React.CSSProperties =
    position === "top-center"
      ? { top: "2%", left: "50%", transform: `translateX(-50%) translateY(${translateY}px)` }
      : position === "top-left"
      ? { top: "2%", left: "8%", transform: `translateY(${translateY}px)` }
      : { top: "2%", right: "8%", transform: `translateY(${translateY}px)` };

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
