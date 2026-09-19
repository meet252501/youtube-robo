import * as React from "react";
import { AbsoluteFill, staticFile, OffthreadVideo, useCurrentFrame, useVideoConfig, spring, interpolate, Easing } from "remotion";
import type { ShortVideoProps } from "../lib/types";
import { Subtitles } from "./Subtitles";
import { HookOverlay } from "./HookOverlay";
import { VideoEffects } from "./VideoEffects";
import { ProgressBar } from "./ProgressBar";
import { FilmTexture } from "./FilmTexture";
import { AudioVisualizer } from "./AudioVisualizer";
import { FocusBadge } from "./FocusBadge";
import { HDRBloomDef, ColorGradeOverlay } from "./ColorGrading";
import { DataInfographics } from "./DataInfographics";
import { BRollOverlay } from "./BRollOverlay";

/**
 * Main 15-story composition that layers all professional post-processing
 * on top of the base video with frame-accurate OffthreadVideo rendering.
 */
export const ShortVideo: React.FC<Record<string, unknown>> = (rawProps: Record<string, unknown>) => {
  const {
    videoUrl,
    subtitles,
    hook,
    effects,
    progressBar,
    filmTexture,
    audioVisualizer,
    focusBadge,
    colorGrading,
    dataVisualization,
    brollCutaways,
  } = rawProps as unknown as ShortVideoProps;
    
  // Resolve local files for Remotion
  const src = videoUrl.startsWith("http") ? videoUrl : staticFile(videoUrl);
  
  const { cameraMoves } = rawProps as unknown as ShortVideoProps;
  
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Floor 9: Saliency-Guided Camera Engine
  // Calculate dynamic scale based on the AI's requested cameraMoves.
  let currentScale = 1.0;
  if (cameraMoves && cameraMoves.length > 0) {
    // Find the latest camera move that has started
    const currentTimeSec = frame / fps;
    let activeMove = null;
    let previousScale = 1.0;
    
    for (let i = 0; i < cameraMoves.length; i++) {
      if (currentTimeSec >= cameraMoves[i].timestampStart) {
        activeMove = cameraMoves[i];
        if (i > 0) {
          // If we had a previous move, ideally we'd track its final state, but let's assume it finished.
          // For a robust engine, we just take the scaleTarget of the previous move as the new base.
          previousScale = cameraMoves[i-1].scaleTarget;
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
        // Linear slow push (Ken Burns)
        currentScale = interpolate(
          frame,
          [moveStartFrame, moveStartFrame + durationFrames],
          [previousScale, activeMove.scaleTarget],
          { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.ease) }
        );
      }
    }
  }

  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      {/* Optional HDR Bloom SVG Definition */}
      {colorGrading?.hdrBloom && <HDRBloomDef />}

      {/* Layer 1: Base video with dynamic Floor 9 Camera Engine and HDR Bloom */}
      <AbsoluteFill style={{ transform: `scale(${currentScale})`, transformOrigin: "center center" }}>
        <VideoEffects config={effects} customFilter={colorGrading?.hdrBloom ? "url(#hdr-bloom)" : undefined}>
          <OffthreadVideo
            src={src}
            style={{ width: "100%", height: "100%", objectFit: "cover" }}
          />
        </VideoEffects>
      </AbsoluteFill>

      {/* Layer 1.5: Cinematic LUT Gradient Overlay */}
      {colorGrading?.enabled && <ColorGradeOverlay config={colorGrading} />}

      {/* Layer 2: Tactile Film Texture (Grain & Vignette) */}
      <FilmTexture config={filmTexture} />

      {/* Layer 3: Audio Visualizer Soundwave */}
      <AudioVisualizer config={audioVisualizer} />

      {/* Layer 3.5: AI B-Roll Context Injection */}
      {brollCutaways && brollCutaways.length > 0 && <BRollOverlay cutaways={brollCutaways} />}

      {/* Layer 4: Multi-Font Semantic Multi-Color Subtitles */}
      {subtitles && <Subtitles config={subtitles} />}

      {/* Layer 4.5: Floor 7 Dynamic Data Infographics */}
      {dataVisualization && <DataInfographics config={dataVisualization} />}

      {/* Layer 5: Floor 3 Minimalist Focus Topic Badge (optional) */}
      {focusBadge && <FocusBadge config={focusBadge} />}

      {/* Layer 6: Viral Hook Overlay Headline (optional) */}
      {hook && <HookOverlay config={hook} />}

      {/* Layer 7: Minimalist Progress Bar */}
      {progressBar && <ProgressBar config={progressBar} />}
    </AbsoluteFill>
  );
};

