import React from "react";
import { AbsoluteFill } from "remotion";
import type { ColorGradingConfig } from "../lib/types";

/**
 * Injects the SVG filter definition for HDR Bloom.
 * This is mounted once globally in the composition so that VideoEffects can reference `url(#hdr-bloom)`.
 */
export const HDRBloomDef: React.FC = () => {
  return (
    <svg style={{ position: "absolute", width: 0, height: 0 }} aria-hidden="true">
      <defs>
        <filter id="hdr-bloom" colorInterpolationFilters="sRGB">
          {/* Step 1: Isolate the bright areas (thresholding) */}
          <feColorMatrix
            type="matrix"
            values="
              2 0 0 0 -0.5
              0 2 0 0 -0.5
              0 0 2 0 -0.5
              0 0 0 1 0"
            in="SourceGraphic"
            result="brightRegions"
          />
          {/* Step 2: Blur the bright areas heavily to create the bloom spread */}
          <feGaussianBlur in="brightRegions" stdDeviation="25" result="bloomBlur" />
          
          {/* Step 3: Tint and dim the bloom slightly so it doesn't overexpose everything */}
          <feColorMatrix
            type="matrix"
            values="
              1.2 0   0   0 0
              0   1.0 0   0 0
              0   0   0.8 0 0
              0   0   0   0.8 0"
            in="bloomBlur"
            result="coloredBloom"
          />
          
          {/* Step 4: Blend the bloom back over the original image using screen */}
          <feBlend in="SourceGraphic" in2="coloredBloom" mode="screen" />
        </filter>
      </defs>
    </svg>
  );
};

export const ColorGradeOverlay: React.FC<{ config: ColorGradingConfig }> = ({ config }) => {
  if (!config.enabled) return null;

  const getGradientForStyle = (style: string) => {
    switch (style) {
      case "teal-orange":
        // Classic Hollywood: Cool shadows, warm highlights
        return "linear-gradient(135deg, rgba(0, 80, 120, 1) 0%, rgba(255, 140, 0, 1) 100%)";
      case "moody-dark":
        // Intellectual/Serious: Desaturated cool blue/green
        return "linear-gradient(to bottom, rgba(20, 30, 40, 1) 0%, rgba(5, 10, 15, 1) 100%)";
      case "vibrant-pop":
        // Energetic: Magenta and Yellow
        return "linear-gradient(45deg, rgba(255, 0, 128, 1) 0%, rgba(255, 200, 0, 1) 100%)";
      case "vintage-film":
        // Nostalgic: Sepia tones with lifted blacks
        return "linear-gradient(to top, rgba(80, 50, 20, 1) 0%, rgba(200, 180, 140, 1) 100%)";
      default:
        return "transparent";
    }
  };

  const getBlendModeForStyle = (style: string): React.CSSProperties["mixBlendMode"] => {
    switch (style) {
      case "teal-orange":
      case "vibrant-pop":
        return "soft-light";
      case "moody-dark":
        return "overlay";
      case "vintage-film":
        return "color";
      default:
        return "soft-light";
    }
  };

  const intensity = config.intensity ?? 0.5;
  const gradient = getGradientForStyle(config.style || "teal-orange");
  const blendMode = getBlendModeForStyle(config.style || "teal-orange");

  return (
    <AbsoluteFill
      style={{
        background: gradient,
        mixBlendMode: blendMode,
        opacity: intensity,
        pointerEvents: "none", // ensure it doesn't block interactions
      }}
    />
  );
};
