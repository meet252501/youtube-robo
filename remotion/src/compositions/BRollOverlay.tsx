import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig, Img, interpolate, staticFile } from "remotion";
import type { BRollCutaway } from "../lib/types";

export const BRollOverlay: React.FC<{ cutaways: BRollCutaway[] }> = ({ cutaways }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const currentTimeSec = frame / fps;

  // Find the active cutaway
  const activeCutaway = cutaways.find(
    (c) => currentTimeSec >= c.timestampStart && currentTimeSec <= c.timestampStart + c.duration
  );

  if (!activeCutaway) {
    return null;
  }

  const startFrame = activeCutaway.timestampStart * fps;
  const endFrame = (activeCutaway.timestampStart + activeCutaway.duration) * fps;

  // Fade in and fade out over 15 frames (0.5s at 30fps)
  const opacity = interpolate(
    frame,
    [startFrame, startFrame + 15, endFrame - 15, endFrame],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  // Slow Ken Burns push in
  const scale = interpolate(
    frame,
    [startFrame, endFrame],
    [1.0, 1.15],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <AbsoluteFill style={{ opacity }}>
      <AbsoluteFill style={{ transform: `scale(${scale})`, transformOrigin: "center center" }}>
        <Img 
          src={staticFile(activeCutaway.url)} 
          style={{ width: "100%", height: "100%", objectFit: "cover" }} 
        />
      </AbsoluteFill>
      
      {/* Cinematic vignette to blend the edges with subtitles */}
      <AbsoluteFill
        style={{
          background: "radial-gradient(circle, rgba(0,0,0,0) 40%, rgba(0,0,0,0.8) 100%)",
          pointerEvents: "none",
        }}
      />
    </AbsoluteFill>
  );
};
