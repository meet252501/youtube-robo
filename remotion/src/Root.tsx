import * as React from "react";
import { Composition } from "remotion";
import { ShortVideo } from "./compositions/ShortVideo";
import type { ShortVideoProps } from "./lib/types";
import { shortVideoPropsSchema } from "./lib/types";

import testProps from "../test_props.json";

const DEFAULT_PROPS = testProps as unknown as ShortVideoProps;
export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="ShortVideo"
        schema={shortVideoPropsSchema}
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
    </>
  );
};
