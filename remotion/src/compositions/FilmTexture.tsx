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

  const { grainOpacity = 0.05, vignetteOpacity = 0.3, textureType = "grain" } = config;

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

      {/* 2. Texture Overlay (Grain or Paper) */}
      {grainOpacity > 0 && textureType === "grain" && (
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

      {/* 3. Paper Texture (Halftone/Creases) */}
      {grainOpacity > 0 && textureType === "paper" && (
        <svg
          style={{
            position: "absolute",
            inset: 0,
            width: "100%",
            height: "100%",
            opacity: grainOpacity * 2, // Paper needs to be slightly more visible
            mixBlendMode: "multiply", // Darkens for a printed halftone look
            filter: "contrast(1.5) sepia(0.2)",
          }}
        >
          <filter id="paper-texture">
            {/* Low freq for crinkles/creases */}
            <feTurbulence
              type="fractalNoise"
              baseFrequency="0.01 0.02"
              numOctaves="4"
              seed="5"
              result="clouds"
            />
            {/* High freq for paper tooth/halftone dots */}
            <feTurbulence
              type="fractalNoise"
              baseFrequency="0.4"
              numOctaves="2"
              seed="1"
              result="noise"
            />
            {/* Blend them */}
            <feBlend in="clouds" in2="noise" mode="screen" result="blend" />
            <feColorMatrix type="matrix" values="
              1 0 0 0 0
              0 0.95 0 0 0
              0 0.9 0 0 0
              0 0 0 1.5 0" in="blend" result="colored" />
          </filter>
          <rect
            width="100%"
            height="100%"
            fill="#fff"
            filter="url(#paper-texture)"
          />
        </svg>
      )}
    </AbsoluteFill>
  );
};
