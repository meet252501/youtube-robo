import { z } from "zod";

// --- Word-level caption ---
export interface CaptionWord {
  text: string;
  startMs: number;
  endMs: number;
}

// --- Subtitle config ---
export type SubtitleAnimation = "none" | "word-highlight" | "pop" | "karaoke" | "bounce" | "rotate" | "kinetic-slam" | "editorial-emphasis" | "karaoke-fill" | "neon-glow" | "pill-karaoke" | "weight-shift";
export type SubtitlePosition = "top" | "middle" | "bottom";

export interface SubtitleStyle {
  fontFamily: string;
  fontSize: number;
  fontColor: string;
  highlightColor: string;
  borderColor: string;
  borderWidth: number;
  bgColor: string;
  bgOpacity: number;
  animation: SubtitleAnimation;
  emphasisWords?: string[];
  semanticColorMap?: Record<string, string>;
  dimInactiveWords?: boolean;
  activeWordScale?: number;
}

export interface SubtitleConfig {
  captions: CaptionWord[];
  position: SubtitlePosition;
  style: SubtitleStyle;
}

// --- Hook config ---
export type HookPosition = "top" | "center" | "bottom";
export type HookSize = "S" | "M" | "L";
export type HookEntrance = "spring" | "fade" | "slide-up" | "none";

export type HookStyle =
  | "classic"
  | "dark"
  | "yellow"
  | "red"
  | "outline"
  | "outline_yellow";

export interface HookConfig {
  text: string;
  position: HookPosition;
  size: HookSize;
  entranceAnimation: HookEntrance;
  displayDurationSec: number;
  style?: HookStyle;
}

// --- Effects config ---
export interface EffectSegment {
  startSec: number;
  endSec: number;
  zoom: number;
  zoomCenterX: number;
  zoomCenterY: number;
  brightness: number;
  contrast: number;
  saturate: number;
}

export interface EffectsConfig {
  segments: EffectSegment[];
}

// --- Color Grading & LUT config ---
export interface ColorGradingConfig {
  enabled?: boolean;
  style?: "teal-orange" | "moody-dark" | "vibrant-pop" | "vintage-film" | string;
  hdrBloom?: boolean;
  intensity?: number;
}

// --- Progress Bar config ---
export interface ProgressBarConfig {
  enabled?: boolean;
  position?: "top" | "bottom";
  height?: number;
  color?: string;
  backgroundColor?: string;
  glow?: boolean;
}

// --- Emoji Stickers config ---
export interface EmojiItem {
  emoji: string;
  startMs: number;
  durationMs?: number;
  position?: "center-left" | "center-right" | "top-right" | "top-left" | "above-captions" | "bottom-center";
  size?: number;
}

export interface EmojiConfig {
  items: EmojiItem[];
}

// --- Film Texture config ---
export interface FilmTextureConfig {
  enabled?: boolean;
  grainOpacity?: number;
  vignetteOpacity?: number;
}

// --- Audio Visualizer config ---
export interface AudioVisualizerConfig {
  enabled?: boolean;
  barCount?: number;
  color?: string;
  position?: "bottom-center" | "bottom-left" | "bottom-right";
  height?: number;
  width?: number;
}

// --- Floor 3: Focus Topic Badge config ---
export interface FocusBadgeConfig {
  enabled?: boolean;
  text: string;
  category?: "insight" | "metric" | "principle" | "alert" | "custom";
  accentColor?: string;
  position?: "top-center" | "top-left" | "top-right";
  startMs?: number;
  durationMs?: number;
}

// --- Main composition props ---
export interface ShortVideoProps {
  videoUrl: string;
  durationInFrames: number;
  fps: number;
  width: number;
  height: number;
  subtitles: SubtitleConfig | null;
  hook: HookConfig | null;
  effects: EffectsConfig | null;
  progressBar?: ProgressBarConfig | null;
  emojis?: EmojiConfig | null;
  filmTexture?: FilmTextureConfig | null;
  audioVisualizer?: AudioVisualizerConfig | null;
  focusBadge?: FocusBadgeConfig | null;
  colorGrading?: ColorGradingConfig | null;
}

// --- Zod schemas for validation (used by render service) ---
export const captionWordSchema = z.object({
  text: z.string(),
  startMs: z.number(),
  endMs: z.number(),
});

export const subtitleStyleSchema = z.object({
  fontFamily: z.string(),
  fontSize: z.number(),
  fontColor: z.string(),
  highlightColor: z.string(),
  borderColor: z.string(),
  borderWidth: z.number(),
  bgColor: z.string(),
  bgOpacity: z.number().min(0).max(1),
  animation: z.enum(["none", "word-highlight", "pop", "karaoke", "bounce", "rotate", "kinetic-slam", "editorial-emphasis", "karaoke-fill", "neon-glow", "pill-karaoke", "weight-shift"]),
});

export const subtitleConfigSchema = z.object({
  captions: z.array(captionWordSchema),
  position: z.enum(["top", "middle", "bottom"]),
  style: subtitleStyleSchema,
});

export const hookConfigSchema = z.object({
  text: z.string(),
  position: z.enum(["top", "center", "bottom"]),
  size: z.enum(["S", "M", "L"]),
  entranceAnimation: z.enum(["spring", "fade", "slide-up", "none"]),
  displayDurationSec: z.number().positive(),
  style: z.enum(["classic", "dark", "yellow", "red", "outline", "outline_yellow"]).optional(),
});

export const effectSegmentSchema = z.object({
  startSec: z.number().min(0),
  endSec: z.number().positive(),
  zoom: z.number().min(0.5).max(3),
  zoomCenterX: z.number().min(0).max(1),
  zoomCenterY: z.number().min(0).max(1),
  brightness: z.number().min(0).max(3),
  contrast: z.number().min(0).max(3),
  saturate: z.number().min(0).max(3),
});

export const effectsConfigSchema = z.object({
  segments: z.array(effectSegmentSchema),
});

export const progressBarConfigSchema = z.object({
  enabled: z.boolean().optional(),
  position: z.enum(["top", "bottom"]).optional(),
  height: z.number().optional(),
  color: z.string().optional(),
  backgroundColor: z.string().optional(),
  glow: z.boolean().optional(),
});

export const emojiItemSchema = z.object({
  emoji: z.string(),
  startMs: z.number(),
  durationMs: z.number().optional(),
  position: z.enum(["center-left", "center-right", "top-right", "top-left", "above-captions", "bottom-center"]).optional(),
  size: z.number().optional(),
});

export const emojiConfigSchema = z.object({
  items: z.array(emojiItemSchema),
});

export const filmTextureConfigSchema = z.object({
  enabled: z.boolean().optional(),
  grainOpacity: z.number().min(0).max(1).optional(),
  vignetteOpacity: z.number().min(0).max(1).optional(),
});

export const audioVisualizerConfigSchema = z.object({
  enabled: z.boolean().optional(),
  barCount: z.number().optional(),
  color: z.string().optional(),
  position: z.enum(["bottom-center", "bottom-left", "bottom-right"]).optional(),
  height: z.number().optional(),
  width: z.number().optional(),
});

export const focusBadgeConfigSchema = z.object({
  enabled: z.boolean().optional(),
  text: z.string(),
  category: z.enum(["insight", "metric", "principle", "alert", "custom"]).optional(),
  accentColor: z.string().optional(),
  position: z.enum(["top-center", "top-left", "top-right"]).optional(),
  startMs: z.number().optional(),
  durationMs: z.number().optional(),
});

export const shortVideoPropsSchema = z.object({
  videoUrl: z.string(),
  durationInFrames: z.number().int().positive(),
  fps: z.number().positive(),
  width: z.number().int().positive(),
  height: z.number().int().positive(),
  subtitles: subtitleConfigSchema.nullable(),
  hook: hookConfigSchema.nullable(),
  effects: effectsConfigSchema.nullable(),
  progressBar: progressBarConfigSchema.nullable().optional(),
  emojis: emojiConfigSchema.nullable().optional(),
  filmTexture: filmTextureConfigSchema.nullable().optional(),
  audioVisualizer: audioVisualizerConfigSchema.nullable().optional(),
  focusBadge: focusBadgeConfigSchema.nullable().optional(),
});

