import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";
import { noise2D } from "@remotion/noise";
import type { FilmTextureConfig } from "../lib/types";

interface FilmTextureProps {
  config?: FilmTextureConfig | null;
}

export const FilmTexture: React.FC<FilmTextureProps> = ({ config }) => {
  const frame = useCurrentFrame();

  if (!config || config.enabled === false) {
    return null;
  }

  const { grainOpacity = 0.05, vignetteOpacity = 0.3 } = config;

  // Generate subtle dynamic procedural noise offset
  const grainSeed = (frame % 10) * 0.1;

  return (
    <AbsoluteFill
      style={{
        pointerEvents: "none",
        zIndex: 25,
      }}
    >
      {/* 1. Subtle Vignette */}
      {vignetteOpacity > 0 && (
        <div
          style={{
            position: "absolute",
            inset: 0,
            background:
              "radial-gradient(circle at center, rgba(0,0,0,0) 55%, rgba(0,0,0,0.8) 100%)",
            opacity: vignetteOpacity,
          }}
        />
      )}

      {/* 2. Micro Film Grain using SVG filter */}
      {grainOpacity > 0 && (
        <svg
          style={{
            position: "absolute",
            inset: 0,
            width: "100%",
            height: "100%",
            opacity: grainOpacity,
            mixBlendMode: "overlay",
          }}
        >
          <filter id={`noise-${frame % 4}`}>
            <feTurbulence
              type="fractalNoise"
              baseFrequency="0.8"
              numOctaves="3"
              seed={frame % 60}
            />
            <feColorMatrix type="saturate" values="0" />
          </filter>
          <rect
            width="100%"
            height="100%"
            filter={`url(#noise-${frame % 4})`}
          />
        </svg>
      )}
    </AbsoluteFill>
  );
};
