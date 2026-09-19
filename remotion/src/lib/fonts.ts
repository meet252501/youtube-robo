import { staticFile } from "remotion";

// === GOOGLE FONT IMPORTS ===
// Bold Sans-Serif (Primary captions)
import { loadFont as loadMontserrat } from "@remotion/google-fonts/Montserrat";
import { loadFont as loadPoppins } from "@remotion/google-fonts/Poppins";
import { loadFont as loadInter } from "@remotion/google-fonts/Inter";
import { loadFont as loadOswald } from "@remotion/google-fonts/Oswald";
import { loadFont as loadAnton } from "@remotion/google-fonts/Anton";
import { loadFont as loadBebas } from "@remotion/google-fonts/BebasNeue";
import { loadFont as loadRoboto } from "@remotion/google-fonts/Roboto";
import { loadFont as loadOpenSans } from "@remotion/google-fonts/OpenSans";
import { loadFont as loadLato } from "@remotion/google-fonts/Lato";
import { loadFont as loadRaleway } from "@remotion/google-fonts/Raleway";
import { loadFont as loadNunito } from "@remotion/google-fonts/Nunito";
import { loadFont as loadWorkSans } from "@remotion/google-fonts/WorkSans";
import { loadFont as loadManrope } from "@remotion/google-fonts/Manrope";
import { loadFont as loadSpaceGrotesk } from "@remotion/google-fonts/SpaceGrotesk";
import { loadFont as loadPlusJakartaSans } from "@remotion/google-fonts/PlusJakartaSans";

// Serif (Elegant, editorial emphasis)
import { loadFont as loadPlayfairDisplay } from "@remotion/google-fonts/PlayfairDisplay";
import { loadFont as loadMerriweather } from "@remotion/google-fonts/Merriweather";
import { loadFont as loadLora } from "@remotion/google-fonts/Lora";
import { loadFont as loadPTSerif } from "@remotion/google-fonts/PTSerif";
import { loadFont as loadLibreBaskerville } from "@remotion/google-fonts/LibreBaskerville";
import { loadFont as loadCormorantGaramond } from "@remotion/google-fonts/CormorantGaramond";
import { loadFont as loadCrimsonText } from "@remotion/google-fonts/CrimsonText";

// Slab Serif
import { loadFont as loadArvo } from "@remotion/google-fonts/Arvo";
import { loadFont as loadRobotoSlab } from "@remotion/google-fonts/RobotoSlab";

// Script/Handwriting (Accent words only)
import { loadFont as loadDancingScript } from "@remotion/google-fonts/DancingScript";
import { loadFont as loadGreatVibes } from "@remotion/google-fonts/GreatVibes";
import { loadFont as loadCaveat } from "@remotion/google-fonts/Caveat";
import { loadFont as loadSacramento } from "@remotion/google-fonts/Sacramento";
import { loadFont as loadPacifico } from "@remotion/google-fonts/Pacifico";
import { loadFont as loadSatisfy } from "@remotion/google-fonts/Satisfy";
import { loadFont as loadKalam } from "@remotion/google-fonts/Kalam";

// Display (Big impact headlines)
import { loadFont as loadLobster } from "@remotion/google-fonts/Lobster";
import { loadFont as loadAbrilFatface } from "@remotion/google-fonts/AbrilFatface";
import { loadFont as loadRighteous } from "@remotion/google-fonts/Righteous";
import { loadFont as loadBungee } from "@remotion/google-fonts/Bungee";
import { loadFont as loadPermanentMarker } from "@remotion/google-fonts/PermanentMarker";
import { loadFont as loadBangers } from "@remotion/google-fonts/Bangers";
import { loadFont as loadFredoka } from "@remotion/google-fonts/Fredoka";
import { loadFont as loadRubikMonoOne } from "@remotion/google-fonts/RubikMonoOne";

// Monospace
import { loadFont as loadFiraCode } from "@remotion/google-fonts/FiraCode";
import { loadFont as loadJetBrainsMono } from "@remotion/google-fonts/JetBrainsMono";
import { loadFont as loadSourceCodePro } from "@remotion/google-fonts/SourceCodePro";

// === FONT CATEGORIES ===
export type FontCategory = "sans" | "serif" | "slab" | "script" | "display" | "mono";

export interface FontEntry {
  name: string;
  family: string;
  category: FontCategory;
  loader: () => void;
  weights: string[];
}

// Master font registry
const FONT_REGISTRY: FontEntry[] = [
  // Sans-Serif
  { name: "Montserrat", family: "Montserrat, sans-serif", category: "sans", loader: () => loadMontserrat("normal", { weights: ["400", "600", "700", "800", "900"], subsets: ["latin"] }), weights: ["400","600","700","800","900"] },
  { name: "Poppins", family: "Poppins, sans-serif", category: "sans", loader: () => loadPoppins("normal", { weights: ["400", "600", "700", "800", "900"], subsets: ["latin"] }), weights: ["400","600","700","800","900"] },
  { name: "Inter", family: "Inter, sans-serif", category: "sans", loader: () => loadInter("normal", { weights: ["400", "600", "700", "800", "900"], subsets: ["latin"] }), weights: ["400","600","700","800","900"] },
  { name: "Oswald", family: "Oswald, sans-serif", category: "sans", loader: () => loadOswald("normal", { weights: ["400", "600", "700"], subsets: ["latin"] }), weights: ["400","600","700"] },
  { name: "Anton", family: "Anton, sans-serif", category: "sans", loader: () => loadAnton("normal", { weights: ["400"], subsets: ["latin"] }), weights: ["400"] },
  { name: "BebasNeue", family: "Bebas Neue, sans-serif", category: "sans", loader: () => loadBebas("normal", { weights: ["400"], subsets: ["latin"] }), weights: ["400"] },
  { name: "Roboto", family: "Roboto, sans-serif", category: "sans", loader: () => loadRoboto("normal", { weights: ["400", "700", "900"], subsets: ["latin"] }), weights: ["400","700","900"] },
  { name: "OpenSans", family: "Open Sans, sans-serif", category: "sans", loader: () => loadOpenSans("normal", { weights: ["400", "600", "700", "800"], subsets: ["latin"] }), weights: ["400","600","700","800"] },
  { name: "Lato", family: "Lato, sans-serif", category: "sans", loader: () => loadLato("normal", { weights: ["400", "700", "900"], subsets: ["latin"] }), weights: ["400","700","900"] },
  { name: "Raleway", family: "Raleway, sans-serif", category: "sans", loader: () => loadRaleway("normal", { weights: ["400", "600", "700", "800", "900"], subsets: ["latin"] }), weights: ["400","600","700","800","900"] },
  { name: "Nunito", family: "Nunito, sans-serif", category: "sans", loader: () => loadNunito("normal", { weights: ["400", "600", "700", "800", "900"], subsets: ["latin"] }), weights: ["400","600","700","800","900"] },
  { name: "WorkSans", family: "Work Sans, sans-serif", category: "sans", loader: () => loadWorkSans("normal", { weights: ["400", "600", "700", "800", "900"], subsets: ["latin"] }), weights: ["400","600","700","800","900"] },
  { name: "Manrope", family: "Manrope, sans-serif", category: "sans", loader: () => loadManrope("normal", { weights: ["400", "600", "700", "800"], subsets: ["latin"] }), weights: ["400","600","700","800"] },
  { name: "SpaceGrotesk", family: "Space Grotesk, sans-serif", category: "sans", loader: () => loadSpaceGrotesk("normal", { weights: ["400", "600", "700"], subsets: ["latin"] }), weights: ["400","600","700"] },
  { name: "PlusJakartaSans", family: "Plus Jakarta Sans, sans-serif", category: "sans", loader: () => loadPlusJakartaSans("normal", { weights: ["400", "600", "700", "800"], subsets: ["latin"] }), weights: ["400","600","700","800"] },

  // Serif
  { name: "PlayfairDisplay", family: "Playfair Display, serif", category: "serif", loader: () => loadPlayfairDisplay("normal", { weights: ["400", "700", "900"], subsets: ["latin"] }), weights: ["400","700","900"] },
  { name: "Merriweather", family: "Merriweather, serif", category: "serif", loader: () => loadMerriweather("normal", { weights: ["400", "700", "900"], subsets: ["latin"] }), weights: ["400","700","900"] },
  { name: "Lora", family: "Lora, serif", category: "serif", loader: () => loadLora("normal", { weights: ["400", "600", "700"], subsets: ["latin"] }), weights: ["400","600","700"] },
  { name: "PTSerif", family: "PT Serif, serif", category: "serif", loader: () => loadPTSerif("normal", { weights: ["400", "700"], subsets: ["latin"] }), weights: ["400","700"] },
  { name: "LibreBaskerville", family: "Libre Baskerville, serif", category: "serif", loader: () => loadLibreBaskerville("normal", { weights: ["400", "700"], subsets: ["latin"] }), weights: ["400","700"] },
  { name: "CormorantGaramond", family: "Cormorant Garamond, serif", category: "serif", loader: () => loadCormorantGaramond("normal", { weights: ["400", "600", "700"], subsets: ["latin"] }), weights: ["400","600","700"] },
  { name: "CrimsonText", family: "Crimson Text, serif", category: "serif", loader: () => loadCrimsonText("normal", { weights: ["400", "600", "700"], subsets: ["latin"] }), weights: ["400","600","700"] },
  { name: "AbrilFatface", family: "Abril Fatface, serif", category: "serif", loader: () => loadAbrilFatface("normal", { weights: ["400"], subsets: ["latin"] }), weights: ["400"] },

  // Slab Serif
  { name: "Arvo", family: "Arvo, serif", category: "slab", loader: () => loadArvo("normal", { weights: ["400", "700"], subsets: ["latin"] }), weights: ["400","700"] },
  { name: "RobotoSlab", family: "Roboto Slab, serif", category: "slab", loader: () => loadRobotoSlab("normal", { weights: ["400", "700", "900"], subsets: ["latin"] }), weights: ["400","700","900"] },

  // Script/Handwriting
  { name: "DancingScript", family: "Dancing Script, cursive", category: "script", loader: () => loadDancingScript("normal", { weights: ["400", "700"], subsets: ["latin"] }), weights: ["400","700"] },
  { name: "GreatVibes", family: "Great Vibes, cursive", category: "script", loader: () => loadGreatVibes("normal", { weights: ["400"], subsets: ["latin"] }), weights: ["400"] },
  { name: "Caveat", family: "Caveat, cursive", category: "script", loader: () => loadCaveat("normal", { weights: ["400", "700"], subsets: ["latin"] }), weights: ["400","700"] },
  { name: "Sacramento", family: "Sacramento, cursive", category: "script", loader: () => loadSacramento("normal", { weights: ["400"], subsets: ["latin"] }), weights: ["400"] },
  { name: "Pacifico", family: "Pacifico, cursive", category: "script", loader: () => loadPacifico("normal", { weights: ["400"], subsets: ["latin"] }), weights: ["400"] },
  { name: "Satisfy", family: "Satisfy, cursive", category: "script", loader: () => loadSatisfy("normal", { weights: ["400"], subsets: ["latin"] }), weights: ["400"] },
  { name: "Kalam", family: "Kalam, cursive", category: "script", loader: () => loadKalam("normal", { weights: ["400", "700"], subsets: ["latin"] }), weights: ["400","700"] },

  // Display
  { name: "Lobster", family: "Lobster, cursive", category: "display", loader: () => loadLobster("normal", { weights: ["400"], subsets: ["latin"] }), weights: ["400"] },
  { name: "Righteous", family: "Righteous, cursive", category: "display", loader: () => loadRighteous("normal", { weights: ["400"], subsets: ["latin"] }), weights: ["400"] },
  { name: "Bungee", family: "Bungee, cursive", category: "display", loader: () => loadBungee("normal", { weights: ["400"], subsets: ["latin"] }), weights: ["400"] },
  { name: "PermanentMarker", family: "Permanent Marker, cursive", category: "display", loader: () => loadPermanentMarker("normal", { weights: ["400"], subsets: ["latin"] }), weights: ["400"] },
  { name: "Bangers", family: "Bangers, cursive", category: "display", loader: () => loadBangers("normal", { weights: ["400"], subsets: ["latin"] }), weights: ["400"] },
  { name: "Fredoka", family: "Fredoka, cursive", category: "display", loader: () => loadFredoka("normal", { weights: ["400", "600", "700"], subsets: ["latin"] }), weights: ["400","600","700"] },
  { name: "RubikMonoOne", family: "Rubik Mono One, sans-serif", category: "display", loader: () => loadRubikMonoOne("normal", { weights: ["400"], subsets: ["latin"] }), weights: ["400"] },

  // Monospace
  { name: "FiraCode", family: "Fira Code, monospace", category: "mono", loader: () => loadFiraCode("normal", { weights: ["400", "700"], subsets: ["latin"] }), weights: ["400","700"] },
  { name: "JetBrainsMono", family: "JetBrains Mono, monospace", category: "mono", loader: () => loadJetBrainsMono("normal", { weights: ["400", "700"], subsets: ["latin"] }), weights: ["400","700"] },
  { name: "SourceCodePro", family: "Source Code Pro, monospace", category: "mono", loader: () => loadSourceCodePro("normal", { weights: ["400", "700"], subsets: ["latin"] }), weights: ["400","700"] },
];

// === PUBLIC API ===

/** Get all registered fonts */
export function getAllFonts(): FontEntry[] {
  return FONT_REGISTRY;
}

/** Get fonts by category */
export function getFontsByCategory(category: FontCategory): FontEntry[] {
  return FONT_REGISTRY.filter((f) => f.category === category);
}

/** Find a specific font by name */
export function getFont(name: string): FontEntry | undefined {
  return FONT_REGISTRY.find((f) => f.name === name);
}

/** Load a font by name and return its CSS family string */
export function loadAndGetFamily(name: string): string {
  const entry = getFont(name);
  if (entry) {
    try { entry.loader(); } catch (e) { console.error("Failed to load font:", name, e); }
    return entry.family;
  }
  // Fallback: try the old SUBTITLE_FONTS map
  return SUBTITLE_FONTS[name] ?? name;
}

// Legacy compat
export const NOTO_SERIF_FONT_FAMILY = "NotoSerif-Bold";
export const notoSerifFontFace = `
@font-face {
  font-family: '${NOTO_SERIF_FONT_FAMILY}';
  src: url('${staticFile("fonts/NotoSerif-Bold.ttf")}') format('truetype');
  font-weight: 700;
  font-style: normal;
}
`;

export const SUBTITLE_FONTS: Record<string, string> = {};
FONT_REGISTRY.forEach((f) => { SUBTITLE_FONTS[f.name] = f.family; });
// Add legacy system fonts
Object.assign(SUBTITLE_FONTS, {
  Verdana: "Verdana, Geneva, sans-serif",
  Arial: "Arial, Helvetica, sans-serif",
  Impact: "Impact, Haettenschweiler, sans-serif",
  Helvetica: "Helvetica, Arial, sans-serif",
  Georgia: "Georgia, 'Times New Roman', serif",
  "Courier New": "'Courier New', Courier, monospace",
});

export function getFontStack(fontFamily: string): string {
  return loadAndGetFamily(fontFamily);
}

// === CURATED FONT SETS (for per-word kinetic typography) ===
export interface FontSet {
  name: string;
  primary: string;      // Bold sans for main words
  emphasis: string;      // Display/serif for IMPACT words
  accent: string;        // Script/handwriting for small filler words
  highlight: string;     // Color accent font
}

export const FONT_SETS: FontSet[] = [
  {
    name: "editorial",
    primary: "Montserrat",
    emphasis: "PlayfairDisplay",
    accent: "DancingScript",
    highlight: "AbrilFatface",
  },
  {
    name: "luxury-editorial",
    primary: "Montserrat",
    emphasis: "PlayfairDisplay",
    accent: "CormorantGaramond",
    highlight: "Lora",
  },
  {
    name: "swiss-minimalist",
    primary: "Inter",
    emphasis: "PlusJakartaSans",
    accent: "Caveat",
    highlight: "SpaceGrotesk",
  },
  {
    name: "bold-modern",
    primary: "Anton",
    emphasis: "BebasNeue",
    accent: "GreatVibes",
    highlight: "Oswald",
  },
  {
    name: "cyber",
    primary: "SpaceGrotesk",
    emphasis: "JetBrainsMono",
    accent: "FiraCode",
    highlight: "RubikMonoOne",
  },
  {
    name: "impact-meme",
    primary: "Bangers",
    emphasis: "AbrilFatface",
    accent: "PermanentMarker",
    highlight: "Righteous",
  },
  {
    name: "handwritten-casual",
    primary: "Fredoka",
    emphasis: "Kalam",
    accent: "Pacifico",
    highlight: "Satisfy",
  },
  {
    name: "modern",
    primary: "Poppins",
    emphasis: "BebasNeue",
    accent: "Caveat",
    highlight: "Oswald",
  },
  {
    name: "cinematic",
    primary: "Inter",
    emphasis: "CormorantGaramond",
    accent: "GreatVibes",
    highlight: "Lora",
  },
  {
    name: "bold",
    primary: "Montserrat",
    emphasis: "Anton",
    accent: "Satisfy",
    highlight: "Bangers",
  },
  {
    name: "elegant",
    primary: "Raleway",
    emphasis: "PlayfairDisplay",
    accent: "Sacramento",
    highlight: "Merriweather",
  },
  {
    name: "tech",
    primary: "SpaceGrotesk",
    emphasis: "RubikMonoOne",
    accent: "Manrope",
    highlight: "FiraCode",
  },
  {
    name: "energetic",
    primary: "WorkSans",
    emphasis: "Bungee",
    accent: "Kalam",
    highlight: "PermanentMarker",
  },
  {
    name: "clean",
    primary: "PlusJakartaSans",
    emphasis: "RobotoSlab",
    accent: "Pacifico",
    highlight: "Righteous",
  },
];

export function getFontSet(name: string): FontSet {
  return FONT_SETS.find((s) => s.name === name) ?? FONT_SETS[0];
}

/** Preload all fonts in a font set */
export function preloadFontSet(set: FontSet): void {
  [set.primary, set.emphasis, set.accent, set.highlight].forEach((fontName) => {
    loadAndGetFamily(fontName);
  });
}
