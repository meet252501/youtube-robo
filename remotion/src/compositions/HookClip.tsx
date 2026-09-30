import * as React from "react";
import {
  AbsoluteFill,
  OffthreadVideo,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  spring,
  interpolate,
  Easing,
} from "remotion";
import type { HookConfig, ColorGradingConfig, FilmTextureConfig } from "../lib/types";
import { HookOverlay } from "./HookOverlay";
import { VideoEffects } from "./VideoEffects";
import { HDRBloomDef, ColorGradeOverlay } from "./ColorGrading";
import { FilmTexture } from "./FilmTexture";
import { ProgressBar } from "./ProgressBar";

/**
 * Floor 4: HookClip — A short Remotion composition that renders ONLY the first
 * N seconds of the video with a hook overlay. Used for the splice-based A/B
 * variant architecture: render body once (hook=null), render 3 hook clips,
 * FFmpeg concat each hook clip onto the body.
 *
 * This composition MUST produce visually identical frames to ShortVideo for the
 * same time range (same video source, same camera moves, same color grading,
 * same film texture) — the ONLY difference is the hook overlay.
 */

export interface HookClipProps {
  videoUrl: string;
  maskUrl?: string | null;
  durationInFrames: number;
  fps: number;
  width: number;
  height: number;
  hook: HookConfig;
  colorGrading?: ColorGradingConfig | null;
  filmTexture?: FilmTextureConfig | null;
  progressBar?: {
    enabled?: boolean;
    position?: "top" | "bottom";
    height?: number;
    color?: string;
    backgroundColor?: string;
    glow?: boolean;
  } | null;
  /** Camera moves from AIDirectorPlan — must match the body render exactly */
  cameraMoves?: {
    timestampStart: number;
    duration: number;
    scaleTarget: number;
    easing: "spring" | "linear";
  }[];
  /** Total duration of the FULL video in frames (for progress bar calculation) */
  fullVideoDurationInFrames: number;
}

export const HookClip: React.FC<Record<string, unknown>> = (
  rawProps: Record<string, unknown>
) => {
  const {
    videoUrl,
    maskUrl,
    hook,
    colorGrading,
    filmTexture,
    progressBar,
    cameraMoves,
  } = rawProps as unknown as HookClipProps;

  const src = videoUrl.startsWith("http") ? videoUrl : staticFile(videoUrl);
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Mirror the exact same camera engine from ShortVideo (Floor 9)
  let currentScale = 1.0;
  if (cameraMoves && cameraMoves.length > 0) {
    const currentTimeSec = frame / fps;
    let activeMove = null;
    let previousScale = 1.0;

    for (let i = 0; i < cameraMoves.length; i++) {
      if (currentTimeSec >= cameraMoves[i].timestampStart) {
        activeMove = cameraMoves[i];
        if (i > 0) {
          previousScale = cameraMoves[i - 1].scaleTarget;
        }
      }
    }

    if (activeMove) {
      const moveStartFrame = activeMove.timestampStart * fps;
      const durationFrames = activeMove.duration * fps;

      if (activeMove.easing === "spring") {
        const spr = spring({
          frame: frame - moveStartFrame,
          fps,
          config: { damping: 14, stiffness: 100, mass: 1 },
        });
        currentScale = interpolate(spr, [0, 1], [previousScale, activeMove.scaleTarget]);
      } else {
        currentScale = interpolate(
          frame,
          [moveStartFrame, moveStartFrame + durationFrames],
          [previousScale, activeMove.scaleTarget],
          {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.out(Easing.ease),
          }
        );
      }
    }
  }

  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      {/* HDR Bloom SVG definition (must match body render) */}
      {colorGrading?.hdrBloom && <HDRBloomDef />}

      {/* Base video with camera engine (mirrors ShortVideo exactly) */}
      <AbsoluteFill
        style={{
          transform: `scale(${currentScale})`,
          transformOrigin: "center center",
        }}
      >
        <VideoEffects
          config={null}
          customFilter={
            colorGrading?.hdrBloom ? "url(#hdr-bloom)" : undefined
          }
        >
          <OffthreadVideo
            src={src}
            style={{ width: "100%", height: "100%", objectFit: "cover" }}
          />
        </VideoEffects>
      </AbsoluteFill>

      {/* 3D Depth mask layer (if mask provided, mirrors ShortVideo) */}
      {maskUrl && (
        <>
          {/* Hook goes behind speaker when mask is present */}
          <HookOverlay config={hook} />
        </>
      )}

      {maskUrl && (
        <AbsoluteFill>
          <svg
            width="100%"
            height="100%"
            style={{ position: "absolute", zIndex: 10 }}
          >
            <defs>
              <mask
                id="luma-mask-hook"
                maskUnits="userSpaceOnUse"
                x="0"
                y="0"
                width="100%"
                height="100%"
              >
                <foreignObject width="100%" height="100%">
                  <OffthreadVideo
                    src={staticFile(maskUrl)}
                    style={{
                      width: "100%",
                      height: "100%",
                      objectFit: "cover",
                      transform: `scale(${currentScale})`,
                      transformOrigin: "center center",
                    }}
                  />
                </foreignObject>
              </mask>
            </defs>
            <foreignObject
              width="100%"
              height="100%"
              mask="url(#luma-mask-hook)"
            >
              <AbsoluteFill
                style={{
                  transform: `scale(${currentScale})`,
                  transformOrigin: "center center",
                }}
              >
                <OffthreadVideo
                  src={src}
                  style={{
                    width: "100%",
                    height: "100%",
                    objectFit: "cover",
                  }}
                />
              </AbsoluteFill>
            </foreignObject>
          </svg>
        </AbsoluteFill>
      )}

      {/* Color grading overlay (must match body) */}
      {colorGrading?.enabled && <ColorGradeOverlay config={colorGrading} />}

      {/* Film texture (must match body) */}
      <FilmTexture config={filmTexture} />

      {/* Hook overlay (foreground if no mask) */}
      {!maskUrl && <HookOverlay config={hook} />}

      {/* Progress bar (must match body — we render it here too for visual continuity) */}
      {progressBar && <ProgressBar config={progressBar} />}
    </AbsoluteFill>
  );
};
