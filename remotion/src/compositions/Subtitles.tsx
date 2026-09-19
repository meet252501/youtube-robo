import React, { useMemo } from "react";
import {
  AbsoluteFill,
  Sequence,
  useCurrentFrame,
  useVideoConfig,
  spring,
  interpolate,
} from "remotion";
import type { SubtitleConfig } from "../lib/types";
import { groupCaptionsIntoBlocks, getActiveWordIndex } from "../lib/captions";
import { getFontStack, getFontSet, FONT_SETS } from "../lib/fonts";
import {
  captionsFromWords,
  createCaptionPages,
  CaptionTrack,
  KineticSlam,
  EditorialEmphasis,
  KaraokeFill,
  NeonGlow,
  PillKaraoke,
  WeightShift,
} from "remotion-captions-kit";

interface SubtitlesProps {
  config: SubtitleConfig;
}

const POSITION_MAP: Record<string, React.CSSProperties> = {
  top: { top: "14%", bottom: "auto" },
  middle: { bottom: "28%", top: "auto" }, // Safe zone: lower-third below the face
  bottom: { bottom: "28%", top: "auto" },
};

export const Subtitles: React.FC<SubtitlesProps> = ({ config }) => {
  const { animation } = config.style;

  // New remotion-captions-kit presets
  if (
    [
      "kinetic-slam",
      "editorial-emphasis",
      "karaoke-fill",
      "neon-glow",
      "pill-karaoke",
      "weight-shift",
    ].includes(animation)
  ) {
    return <KitSubtitles config={config} />;
  }

  // Fallback to our legacy engine for "pop", "bounce", "rotate", "word-highlight", "karaoke", "none"
  return <LegacySubtitles config={config} />;
};

// ==========================================
// NEW: remotion-captions-kit engine
// ==========================================
const KitSubtitles: React.FC<SubtitlesProps> = ({ config }) => {
  const { captions, position, style } = config;

  // 1. Convert to WordTiming
  const words = useMemo(() => {
    return captions.map((c) => ({
      word: c.text,
      start: c.startMs,
      end: c.endMs,
    }));
  }, [captions]);

  // 2. Generate punchy short pages (2-4 words max like OpusClip/CapCut)
  const { pages } = useMemo(() => {
    const res = captionsFromWords({ words, timeUnit: "milliseconds" });
    return createCaptionPages({
      captions: res.captions,
      maxCharsPerPage: 22,
      breakOnPunctuation: true,
      minWordsPerPage: 1,
    });
  }, [words]);

  // 3. Resolve Font Set
  const isFontSet = FONT_SETS.some((s) => s.name === style.fontFamily);
  const fontSet = isFontSet
    ? getFontSet(style.fontFamily)
    : {
        primary: style.fontFamily,
        emphasis: style.fontFamily,
        accent: style.fontFamily,
        highlight: style.fontFamily,
      };

  const primaryFont = getFontStack(fontSet.primary);
  const emphasisFont = getFontStack(fontSet.emphasis);
  const highlightFont = getFontStack(fontSet.highlight);

  // 4. Setup Theme with Safe Zone Position (never covers the face!)
  const theme = {
    fontFamily: primaryFont,
    fontSize: Math.max(66, Math.min(style.fontSize, 74)),
    textColor: style.fontColor,
    activeColor: style.highlightColor,
    pillColor: style.bgColor,
    position: (position === "top" ? "top" : "bottom") as any,
    edgeOffset: position === "top" ? 0.14 : 0.26, // 26% from bottom = golden lower-chest zone
  };

  // 5. Setup Professional Studio Typography Rules & Multi-Color Semantics
  const colorMap = style.semanticColorMap || {};
  const emphasisWordsList = ((style as any).emphasisWords || []).map((w: string) => w.toLowerCase());

  const emphasis = [
    // Rule A: Explicit per-word semantic color map from AI Director (Emerald #00FF88, Volt #FFE600, Coral #FF3B30, Cyan #00F0FF)
    ...Object.entries(colorMap).map(([rawWord, color]) => ({
      words: [rawWord.toLowerCase()],
      style: {
        fontFamily: highlightFont,
        fontWeight: 900,
        textShadow: `0 0 16px ${color}66, 0 3px 6px rgba(0,0,0,0.9)`,
      },
      color,
    })),
    // Rule B: Numbers, percentages, currency metrics -> Emerald Neo (#00FF88)
    {
      match: (token: any) => /[0-9$%]/.test(token.text),
      style: {
        fontFamily: highlightFont,
        fontWeight: 900,
        textShadow: "0 0 16px rgba(0, 255, 136, 0.45), 0 3px 6px rgba(0,0,0,0.9)",
      },
      color: "#00FF88",
    },
    // Rule C: Director's selected emphasis keywords -> Vibrant Highlight Color
    ...(emphasisWordsList.length > 0
      ? [
          {
            words: emphasisWordsList,
            style: {
              fontFamily: highlightFont,
              fontWeight: 900,
              textShadow: `0 0 16px ${style.highlightColor}66, 0 3px 6px rgba(0,0,0,0.9)`,
            },
            color: style.highlightColor,
          },
        ]
      : []),
    // Rule D: ALL CAPS or Key Impact words -> Ultra-Bold with emphasis font
    {
      match: (token: any) =>
        token.text === token.text.toUpperCase() &&
        token.text.match(/[A-Z]/) !== null &&
        token.text.length > 2,
      style: {
        fontFamily: emphasisFont,
        fontWeight: 900,
      },
      color: style.highlightColor,
    },
  ];

  // Base props
  const presetProps = { theme, emphasis };

  return (
    <AbsoluteFill
      style={{
        textShadow: "0 2px 4px rgba(0,0,0,0.85), 0 6px 20px rgba(0,0,0,0.95)",
        paintOrder: "stroke fill",
        WebkitTextStroke: style.borderWidth > 0 ? `${style.borderWidth}px ${style.borderColor}` : undefined,
        letterSpacing: "-0.015em",
      }}
    >
      <CaptionTrack pages={pages}>
        {(page: any) => {
          switch (style.animation) {
            case "kinetic-slam":
              return <KineticSlam page={page} {...presetProps} />;
            case "editorial-emphasis":
              return <EditorialEmphasis page={page} {...presetProps} />;
            case "karaoke-fill":
              return <KaraokeFill page={page} {...presetProps} />;
            case "neon-glow":
              return <NeonGlow page={page} {...presetProps} />;
            case "pill-karaoke":
              return <PillKaraoke page={page} {...presetProps} />;
            case "weight-shift":
              return <WeightShift page={page} {...presetProps} />;
            default:
              return <KineticSlam page={page} {...presetProps} />;
          }
        }}
      </CaptionTrack>
    </AbsoluteFill>
  );
};

// ==========================================
// LEGACY: Our original manual subtitle engine
// ==========================================
const LegacySubtitles: React.FC<SubtitlesProps> = ({ config }) => {
  const { fps } = useVideoConfig();
  const blocks = groupCaptionsIntoBlocks(config.captions);

  return (
    <AbsoluteFill>
      {blocks.map((block, i) => {
        const startFrame = Math.round((block.startMs / 1000) * fps);
        const durationFrames = Math.max(
          1,
          Math.round(((block.endMs - block.startMs) / 1000) * fps)
        );

        return (
          <Sequence
            key={i}
            from={startFrame}
            durationInFrames={durationFrames}
            layout="none"
          >
            <LegacySubtitleBlock
              block={block}
              config={config}
              blockStartMs={block.startMs}
            />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};

interface LegacySubtitleBlockProps {
  block: ReturnType<typeof groupCaptionsIntoBlocks>[number];
  config: SubtitleConfig;
  blockStartMs: number;
}

const LegacySubtitleBlock: React.FC<LegacySubtitleBlockProps> = ({
  block,
  config,
  blockStartMs,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { style, position } = config;

  const currentTimeMs = blockStartMs + (frame / fps) * 1000;
  const activeIndex = getActiveWordIndex(block.words, currentTimeMs);

  const positionStyle = POSITION_MAP[position] ?? POSITION_MAP.bottom;
  const fontStack = getFontStack(style.fontFamily);

  const hasBg = style.bgOpacity > 0;
  const bgStyle: React.CSSProperties = hasBg
    ? {
        backgroundColor: `${style.bgColor}${Math.round(style.bgOpacity * 255)
          .toString(16)
          .padStart(2, "0")}`,
        borderRadius: 8,
        padding: "8px 16px",
      }
    : {};

  return (
    <div
      style={{
        position: "absolute",
        left: 0,
        right: 0,
        display: "flex",
        justifyContent: "center",
        ...positionStyle,
      }}
    >
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          justifyContent: "center",
          gap: "10px 16px",
          maxWidth: "85%",
          ...bgStyle,
        }}
      >
        {block.words.map((word, i) => (
          <LegacyWordSpan
            key={i}
            word={word.text}
            isActive={i === activeIndex}
            style={style}
            fontStack={fontStack}
            animation={style.animation}
            frame={frame}
            fps={fps}
            wordStartMs={word.startMs}
            blockStartMs={blockStartMs}
          />
        ))}
      </div>
    </div>
  );
};

interface LegacyWordSpanProps {
  word: string;
  isActive: boolean;
  style: SubtitleConfig["style"];
  fontStack: string;
  animation: SubtitleConfig["style"]["animation"];
  frame: number;
  fps: number;
  wordStartMs: number;
  blockStartMs: number;
}

const LegacyWordSpan: React.FC<LegacyWordSpanProps> = ({
  word,
  isActive,
  style,
  fontStack,
  animation,
  frame,
  fps,
  wordStartMs,
  blockStartMs,
}) => {
  const wordStartFrame = Math.round(
    ((wordStartMs - blockStartMs) / 1000) * fps
  );

  const cleanWord = word.toLowerCase().replace(/[^a-z0-9$%]/g, "");
  const colorMap = style.semanticColorMap || {};
  const isNumeric = /[0-9$%]/.test(word);
  const isKeyword = cleanWord in colorMap || ((style.emphasisWords || []).map(w => w.toLowerCase()).includes(cleanWord)) || isNumeric;
  const semanticColor = colorMap[cleanWord] || (isNumeric ? "#00FF88" : style.highlightColor);

  let transform = "";
  let color = isKeyword ? semanticColor : style.fontColor;
  let opacity = isActive ? 1 : (style.dimInactiveWords !== false && !isKeyword ? 0.72 : 1);
  let extraStyle: React.CSSProperties = {};

  if (isActive) {
    color = semanticColor || style.highlightColor;
    opacity = 1;

    switch (animation) {
      case "pop": {
        const scale = spring({
          frame: frame - wordStartFrame,
          fps,
          config: { mass: 0.5, stiffness: 500, damping: 15 },
        });
        const scaleValue = interpolate(scale, [0, 1], [0.9, 1.12]);
        transform = `scale(${scaleValue})`;
        extraStyle = {
          textShadow: `0 0 18px ${color}88, 0 3px 6px rgba(0,0,0,0.9)`,
        };
        break;
      }
      case "bounce": {
        const bounce = spring({
          frame: frame - wordStartFrame,
          fps,
          config: { mass: 1, stiffness: 400, damping: 8 },
        });
        const translateY = interpolate(bounce, [0, 0.5, 1], [8, -12, 0]);
        transform = `translateY(${translateY}px)`;
        extraStyle = {
          textShadow: `0 0 18px ${color}88, 0 3px 6px rgba(0,0,0,0.9)`,
        };
        break;
      }
      case "rotate": {
        const rot = spring({
          frame: frame - wordStartFrame,
          fps,
          config: { mass: 0.8, stiffness: 200, damping: 10 },
        });
        const rotateValue = interpolate(rot, [0, 1], [-8, 0]);
        const scaleValue = interpolate(rot, [0, 1], [0.85, 1.1]);
        transform = `rotate(${rotateValue}deg) scale(${scaleValue})`;
        break;
      }
      case "karaoke": {
        extraStyle = {
          backgroundColor: color,
          color: style.bgColor || "#000000",
          borderRadius: 8,
          padding: "4px 10px",
          boxShadow: `0 4px 12px ${color}66`,
        };
        break;
      }
      case "word-highlight": {
        extraStyle = {
          textShadow: `0 0 16px ${color}, 0 0 28px ${color}66`,
        };
        break;
      }
      default: {
        transform = "scale(1.08)";
        extraStyle = {
          textShadow: `0 0 16px ${color}88, 0 3px 6px rgba(0,0,0,0.9)`,
        };
        break;
      }
    }
  }

  return (
    <span
      style={{
        fontFamily: fontStack,
        fontSize: style.fontSize,
        fontWeight: 900,
        textTransform: "none",
        letterSpacing: "0.02em",
        lineHeight: 1.1,
        color: animation === "karaoke" && isActive ? undefined : color,
        WebkitTextStroke: style.borderWidth > 0 ? `${style.borderWidth}px ${style.borderColor}` : undefined,
        textShadow: style.borderWidth > 0 ? "0px 4px 10px rgba(0,0,0,0.8)" : undefined,
        transform,
        display: "inline-block",
        opacity,
        transition: "none",
        ...extraStyle,
      }}
    >
      {word}
    </span>
  );
};
