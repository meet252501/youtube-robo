import React from "react";
import { useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import type { EmojiItem, EmojiConfig } from "../lib/types";

interface EmojiStickersProps {
  config?: EmojiConfig | null;
}

const POSITION_MAP: Record<string, React.CSSProperties> = {
  "center-left": { left: "10%", bottom: "38%" },
  "center-right": { right: "10%", bottom: "38%" },
  "top-right": { right: "8%", top: "14%" },
  "top-left": { left: "8%", top: "14%" },
  "above-captions": { left: "50%", bottom: "40%", transform: "translateX(-50%)" },
  "bottom-center": { left: "50%", bottom: "20%", transform: "translateX(-50%)" },
};

export const EmojiStickers: React.FC<EmojiStickersProps> = ({ config }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  if (!config || !config.items || config.items.length === 0) {
    return null;
  }

  const currentTimeMs = (frame / fps) * 1000;

  // Find active emojis
  const activeItems = config.items.filter((item) => {
    const start = item.startMs;
    const end = item.startMs + (item.durationMs || 1500);
    return currentTimeMs >= start && currentTimeMs <= end;
  });

  if (activeItems.length === 0) {
    return null;
  }

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        pointerEvents: "none",
        zIndex: 45,
      }}
    >
      {activeItems.map((item, index) => {
        const startFrame = Math.round((item.startMs / 1000) * fps);
        const durationFrames = Math.round(((item.durationMs || 1500) / 1000) * fps);
        const elapsedFrames = frame - startFrame;
        const remainingFrames = durationFrames - elapsedFrames;

        // Entrance bounce spring
        const scaleSpring = spring({
          frame: elapsedFrames,
          fps,
          config: {
            damping: 10,
            stiffness: 220,
            mass: 0.8,
          },
        });

        // Exit fade out
        const exitOpacity = interpolate(remainingFrames, [0, 6], [0, 1], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        });

        // Dynamic tilt wiggle
        const rotation = interpolate(elapsedFrames, [0, 5, 12], [-14, 8, 0], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        });

        const posStyle = POSITION_MAP[item.position || "above-captions"] || POSITION_MAP["above-captions"];
        const size = item.size || 110;

        return (
          <div
            key={`${item.emoji}-${index}`}
            style={{
              position: "absolute",
              ...posStyle,
              fontSize: `${size}px`,
              lineHeight: 1,
              transform: `${posStyle.transform || ""} scale(${scaleSpring}) rotate(${rotation}deg)`,
              opacity: exitOpacity,
              filter: "drop-shadow(0 10px 20px rgba(0,0,0,0.5)) drop-shadow(0 0 10px rgba(255,215,0,0.4))",
              userSelect: "none",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            {item.emoji}
          </div>
        );
      })}
    </div>
  );
};
