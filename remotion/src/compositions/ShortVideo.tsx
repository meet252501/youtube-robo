import * as React from "react";
import { AbsoluteFill, staticFile, OffthreadVideo } from "remotion";
import type { ShortVideoProps } from "../lib/types";
import { Subtitles } from "./Subtitles";
import { HookOverlay } from "./HookOverlay";
import { VideoEffects } from "./VideoEffects";
import { ProgressBar } from "./ProgressBar";
import { FilmTexture } from "./FilmTexture";
import { AudioVisualizer } from "./AudioVisualizer";
import { FocusBadge } from "./FocusBadge";

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
  } = rawProps as unknown as ShortVideoProps;
    
  // Resolve local files for Remotion
  const src = videoUrl.startsWith("http") ? videoUrl : staticFile(videoUrl);
  
  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      {/* Layer 1: Base video with optional zoom/color effects */}
      <VideoEffects config={effects}>
        <OffthreadVideo
          src={src}
          style={{ width: "100%", height: "100%", objectFit: "cover" }}
        />
      </VideoEffects>

      {/* Layer 2: Tactile Film Texture (Grain & Vignette) */}
      <FilmTexture config={filmTexture} />

      {/* Layer 3: Audio Visualizer Soundwave */}
      <AudioVisualizer config={audioVisualizer} />

      {/* Layer 4: Multi-Font Semantic Multi-Color Subtitles */}
      {subtitles && <Subtitles config={subtitles} />}

      {/* Layer 5: Floor 3 Minimalist Focus Topic Badge (optional) */}
      {focusBadge && <FocusBadge config={focusBadge} />}

      {/* Layer 6: Viral Hook Overlay Headline (optional) */}
      {hook && <HookOverlay config={hook} />}

      {/* Layer 7: Minimalist Progress Bar */}
      {progressBar && <ProgressBar config={progressBar} />}
    </AbsoluteFill>
  );
};

