import * as React from "react";
import { Composition } from "remotion";
import { ShortVideo } from "./compositions/ShortVideo";
import { HookClip } from "./compositions/HookClip";
import type { ShortVideoProps } from "./lib/types";
import { ShortVideoSchema } from "./lib/types";

import testProps from "../test_props.json";

const DEFAULT_PROPS = testProps as unknown as ShortVideoProps;

export const RemotionRoot: React.FC = () => {
  return (
    <>
      {/* Main full-video composition (renders body with or without hook) */}
      <Composition
        id="ShortVideo"
        schema={ShortVideoSchema}
        component={ShortVideo}
        durationInFrames={DEFAULT_PROPS.durationInFrames}
        fps={DEFAULT_PROPS.fps}
        width={DEFAULT_PROPS.width}
        height={DEFAULT_PROPS.height}
        defaultProps={DEFAULT_PROPS}
        calculateMetadata={({ props }) => ({
          durationInFrames: props.durationInFrames,
          fps: props.fps,
          width: props.width,
          height: props.height,
        })}
      />

      {/* Floor 4: Short hook-only clip for A/B splice architecture */}
      <Composition
        id="HookClip"
        component={HookClip}
        durationInFrames={DEFAULT_PROPS.durationInFrames}
        fps={DEFAULT_PROPS.fps}
        width={DEFAULT_PROPS.width}
        height={DEFAULT_PROPS.height}
        calculateMetadata={({ props }) => ({
          durationInFrames: (props as any).durationInFrames ?? 75,
          fps: (props as any).fps ?? 30,
          width: (props as any).width ?? 1080,
          height: (props as any).height ?? 1920,
        })}
      />
    </>
  );
};
