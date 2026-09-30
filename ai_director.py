import os
import json
import re
import cv2
from typing import Optional, Dict, Any, List
from PIL import Image
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class DataVisualization(BaseModel):
    hasMetrics: bool = Field(description="True if the transcript contains hard numbers, percentages, money, or statistics.")
    metricValue: Optional[str] = Field(default="", description="The primary number or metric (e.g. '91%', '$1M', '3 hours').")
    metricLabel: Optional[str] = Field(default="", description="Short description of the metric (e.g. 'Businesses use video', 'Revenue', 'Sleep lost').")
    chartType: Optional[str] = Field(default="none", description="Type of chart to display: 'counter-gauge', 'data-card', or 'none'.")
    timestampStart: Optional[float] = Field(default=0.0, description="Approximate start time in seconds to show the graphic (e.g., 10.5)")

class CameraMove(BaseModel):
    timestampStart: float = Field(description="Start time in seconds for the camera move (e.g., 12.5)")
    duration: float = Field(description="Duration in seconds (e.g., 0.3 for punch-in, 5.0 for Ken Burns slow push)")
    scaleTarget: float = Field(description="Target scale. 1.0 is default, 1.15 is a typical punch-in, 1.3 is extreme closeup.")
    easing: str = Field(description="Easing function: 'spring' for snappy punch-ins, 'linear' for slow pushes")

class BRollCutaway(BaseModel):
    timestampStart: float = Field(description="Start time in seconds to overlay the B-Roll (e.g. 15.5)")
    duration: float = Field(description="Duration of the B-Roll in seconds (e.g. 2.0)")
    imagePrompt: str = Field(description="A highly descriptive AI image generation prompt for the B-Roll (e.g., 'macro shot of glowing human cells dividing under a microscope, cinematic lighting')")

class EmojiItem(BaseModel):
    emoji: str = Field(description="The actual emoji character (e.g., 🤯, 💰, 📉, 🚀)")
    startMs: float = Field(description="Start time in milliseconds (e.g., 2500)")
    durationMs: float = Field(description="Duration in milliseconds (e.g., 1500)")
    position: str = Field(description="Position: 'center-left', 'center-right', 'top-right', 'top-left', 'above-captions', 'bottom-center'")
    size: int = Field(default=110, description="Font size of the emoji (e.g., 110, 150)")

# ==============================================================================
# FLOOR 3 / 15-STORY ENTERPRISE MULTIMODAL AI CREATIVE DIRECTOR
# ==============================================================================

class FilmTextureConfig(BaseModel):
    enabled: bool = Field(default=False)
    grainOpacity: float = Field(default=0.05)
    vignetteOpacity: float = Field(default=0.3)
    textureType: str = Field(default="grain", description="'grain' for cinematic, 'paper' for Ali Abdaal / documentary style")

class VisualPerception(BaseModel):
    setting: str = Field(description="Visual environment description (e.g. Dark podcast studio, Shure SM7B microphones, warm rim lighting)")
    lightingMood: str = Field(description="Lighting style (e.g. low_key_moody, warm_cinematic, bright_commercial)")
    subjectsAndEquipment: str = Field(description="People, microphones, coffee mugs, papers, framing style")
    hasNativeIntroOrDisclaimer: bool = Field(description="True if video has native disclaimers, titles, or text burned into the top")
    safeZoneRecommendation: str = Field(description="Recommended vertical placement for overlays to avoid occluding faces and mics")

class ConversationalAnalysis(BaseModel):
    primaryVibe: str = Field(description="Dominant conversation vibe (e.g. philosophical_interview, intellectual_dialogue, scientific_breakdown, high_stakes_debate)")
    intellectualDepth: str = Field(description="Degree of depth: philosophical_reflective, tactical_educational, emotional_storytelling, casual_banter")
    emotionalTone: str = Field(description="Emotional atmosphere: contemplative, serious, revelatory, urgent, inspirational")
    coreThesis: str = Field(description="1-sentence synthesis of the philosophical or intellectual insight")
    keyDiscussionTopics: List[str] = Field(description="3-5 core intellectual topics discussed")

class ArtisticDirection(BaseModel):
    fontFamily: str = Field(description="One of: editorial, luxury-editorial, swiss-minimalist, bold-modern, cyber, modern, clean")
    fontRationale: str = Field(description="Why this typography matches the visual studio environment and dialogue tone")
    animation: str = Field(description="Subtitle animation: kinetic-slam, editorial-emphasis, karaoke-fill, pill-karaoke, weight-shift")
    primaryTextColor: str = Field(description="Primary subtitle text hex color, default #FFFFFF")
    highlightColor: str = Field(description="Active spoken word highlight hex color (e.g. #FFD700 for philosophical gold, #FFE600 for volt)")
    progressBarColor: str = Field(description="Harmonious progress bar accent hex color")
    fontSize: int = Field(description="Subtitle font size (66-74px for optimal mobile retention)")
    showTopOverlays: bool = Field(description="Strictly False for studio interviews and videos with native intro disclaimers")
    emphasisWords: List[str] = Field(description="8-15 high-weight conceptual anchor words to emphasize in subtitles")
    colorGradingStyle: str = Field(description="Cinematic LUT style: 'teal-orange', 'moody-dark', 'vibrant-pop', or 'vintage-film'")
    colorGradeLUT: str = Field(default="intellectual_podcast", description="Floor 5: Name of the .cube 3D LUT to apply. One of: intellectual_podcast, philosophical_interview, business_podcast, high_energy, moody_story, scientific_breakdown, vibrant_pop, vintage_film, clean_modern")
    hdrBloom: bool = Field(description="True if the video lighting warrants an HDR bloom effect (glowing highlights)")

class AIDirectorPlan(BaseModel):
    visualPerception: VisualPerception
    conversationalAnalysis: ConversationalAnalysis
    artisticDirection: ArtisticDirection
    directorSummary: str = Field(description="Executive summary of the creative direction and visual-vibe synergy")
    dataVisualization: DataVisualization
    cameraMoves: List[CameraMove] = Field(default=[], description="List of dynamic cinematic camera zoom movements triggered by intense moments in the transcript.")
    brollCutaways: List[BRollCutaway] = Field(default=[], description="List of AI B-Roll cutaways to inject visual context.")
    emojis: List[EmojiItem] = Field(default=[], description="List of floating emojis to pop up for visual engagement (Ali Abdaal / MrBeast style).")
    filmTexture: FilmTextureConfig
    hookVariants: Optional[List[Dict[str, Any]]] = Field(default=None, description="Optional list of generated hook variants for A/B testing")

# Premium Typography Collections (Google Fonts bundled in Remotion)
AVAILABLE_FONT_SETS = [
    "editorial",          # Montserrat + Playfair Display + Dancing Script (Deep podcasts, intellectual interviews, philosophical dialogue)
    "luxury-editorial",   # Montserrat + Playfair Display + Cormorant Garamond (Prestige Vox luxury & documentary style)
    "swiss-minimalist",   # Inter + Plus Jakarta Sans + Caveat (Ali Abdaal clean tech, thought leadership, modern essays)
    "bold-modern",        # Anton + Bebas Neue + Great Vibes (High impact modern viral creator)
    "cyber",              # Space Grotesk + JetBrains Mono + Fira Code (Tech, AI, coding, algorithms)
    "modern",             # Poppins + Bebas Neue + Caveat (General versatile creator)
    "clean"               # Plus Jakarta Sans + Roboto Slab + Pacifico (Corporate clarity)
]

AVAILABLE_ANIMATIONS = [
    "kinetic-slam",       # High impact scale slam with overshoot physics (OpusClip / Hormozi / Podcast Viral)
    "editorial-emphasis", # Serif weight shifting & elegant highlight
    "neon-glow",          # Subtle neon pulsing glow
    "pill-karaoke",       # Bouncing pill badge behind active word
    "karaoke-fill",       # Smooth left-to-right color fill
    "weight-shift"        # Dynamic weight pulse 400->900
]

# Multi-Channel Semantic Color Taxonomy
SEMANTIC_COLOR_PATTERNS = [
    # 1. Financial / Quantitative / Metrics -> Emerald Neo
    (r"\b(\d+|[0-9$%]|money|dollar|dollars|wealth|revenue|cash|rich|profit|income|cost|price|crore|lakh|million|billion|k|percent|percentage|roi)\b", "#00FF88"),
    # 2. Action / Hook / High-Impact Verbs -> Volt Yellow
    (r"\b(secret|power|proven|win|best|fast|now|insane|crazy|super|epic|transform|change|guaranteed)\b", "#FFE600"),
    # 3. Caution / Alert / Negative Impact / Mortality -> Coral Flame
    (r"\b(danger|wrong|mistake|avoid|fatal|fail|ruin|dead|death|die|risk|warning|problem|toxic|stop|never)\b", "#FF3B30"),
    # 4. Core Science / Biology / Longevity / Tech -> Cyber Cyan
    (r"\b(fasting|body|longevity|health|age|young|diet|biology|cell|cells|dna|ai|code|data|system|truth|algorithm)\b", "#00F0FF"),
    # 5. Philosophical Depth / Wisdom / Elite -> Warm Polished Gold
    (r"\b(philosophy|mind|life|live|specifics|master|purpose|meaning|soul|principle|human|wisdom|exist|reason)\b", "#FFD700"),
]

def extract_video_keyframes(video_path: str, num_frames: int = 5) -> List[Image.Image]:
    """
    Extracts 5 strategic RGB keyframes across the video duration for multimodal visual perception:
    - 10%: Hook & intro scene (detects native titles/disclaimers)
    - 25%: Initial speaker framing & lighting
    - 50%: Mid-conversation dynamics & camera angles
    - 75%: Secondary subject / reaction framing
    - 90%: Conclusion & emotional crescendo
    """
    if not video_path or not os.path.exists(video_path):
        return []
    try:
        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames <= 0:
            cap.release()
            return []
        
        positions = [0.10, 0.25, 0.50, 0.75, 0.90] if num_frames == 5 else [0.20, 0.50, 0.80]
        frames = []
        for p in positions:
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(total_frames * p))
            ret, frame = cap.read()
            if ret:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                # Resized for high detail yet ultra-fast token transfer
                pil_img = Image.fromarray(cv2.resize(rgb, (360, 640)))
                frames.append(pil_img)
        cap.release()
        return frames
    except Exception as e:
        print(f"[AI DIRECTOR] Error extracting video keyframes: {e}")
        return []

def build_semantic_color_map(transcript: Dict[str, Any], emphasis_words: List[str]) -> Dict[str, str]:
    """
    Analyzes all spoken words in the transcript and maps keywords to distinct contextual colors.
    """
    color_map: Dict[str, str] = {}
    
    words_list = []
    for segment in transcript.get("segments", []):
        for word in segment.get("words", []):
            clean = re.sub(r"[^\w\s$%]", "", word.get("word", "")).lower().strip()
            if clean:
                words_list.append(clean)

    for w in words_list:
        if w in color_map:
            continue
        for pattern, color in SEMANTIC_COLOR_PATTERNS:
            if re.search(pattern, w):
                color_map[w] = color
                break

    for ew in emphasis_words:
        clean_ew = ew.lower().strip()
        if clean_ew and clean_ew not in color_map:
            color_map[clean_ew] = "#FFD700"  # Polished gold for deep intellectual concepts

    return color_map

def analyze_transcript_and_direct(
    transcript: Dict[str, Any],
    video_path: str = "",
    video_title: str = ""
) -> Dict[str, Any]:
    """
    Enterprise-Grade Multimodal AI Creative Director:
    1. Multi-frame computer vision analysis (lighting, dark studio, microphones, framing, native disclaimers).
    2. Deep transcript analysis (conversational depth, philosophical undertones, pacing, core thesis).
    3. Artistic direction & typography selection matching the detected vibe.
    4. Enforces clean lower-third placement and zero clashing overlays.
    """
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    
    full_text = ""
    if "segments" in transcript:
        full_text = " ".join(s.get("text", "").strip() for s in transcript["segments"])
    elif "text" in transcript:
        full_text = transcript["text"]

    plan: Optional[AIDirectorPlan] = None
    if api_key:
        try:
            client = genai.Client(api_key=api_key)
            model_name = os.environ.get("GEMINI_MODEL") or "gemini-2.5-flash"
            
            keyframes = extract_video_keyframes(video_path, num_frames=5)
            print(f"[AI DIRECTOR] Multimodal Director: Analyzing {len(keyframes)} video keyframes + full transcript...")
            
            prompt = f"""
            You are an elite creative video director specializing in high-retention podcast shorts, intellectual documentaries, and viral video editing (Lex Fridman, Huberman Lab, Ali Abdaal, Vox, Steven Bartlett).
            
            You are provided with:
            1. 5 ACTUAL VIDEO FRAMES sampling the video from start to finish.
            2. The FULL TRANSCRIPT of the dialogue.

            VIDEO TITLE / FILE: {video_title}
            FULL TRANSCRIPT:
            "{full_text}"

            AVAILABLE FONT SETS:
            {json.dumps(AVAILABLE_FONT_SETS, indent=2)}

            AVAILABLE ANIMATIONS:
            {json.dumps(AVAILABLE_ANIMATIONS, indent=2)}

            YOUR MISSION:
            Perform a dual multimodal analysis:
            A. VISUAL PERCEPTION:
               - Inspect the frames carefully. Is this a moody dark studio with podcast microphones (e.g. Shure SM7B), intimate lighting, and seated speakers?
               - Check the intro frames: Does the video already have its own disclaimer, title, or graphic text? (If so, NEVER place clashing overlays over it).
               - What is the visual aesthetic? (e.g. "dark_studio_intimate_podcast", "conference", "talking_head").
            
            B. CONVERSATIONAL ANALYSIS:
               - Deeply analyze the transcript content. Is this a deep philosophical discussion or intellectual interview (e.g., about longevity, health protocols, cellular biology, life expectancy, mindset, life principles)?
               - Identify the primary vibe: "philosophical_interview", "intellectual_dialogue", "scientific_breakdown", etc.
               - Extract 8-15 high-impact conceptual anchor words (e.g., "specifics", "live", "age", "body", "younger", "fasting", "longevity").

            C. ARTISTIC DIRECTION:
               - For Philosophical Interviews / Intellectual Podcasts:
                 * Choose fontFamily "editorial" or "luxury-editorial" (clean, dignified, premium serif/sans pairings).
                 * Animation: "kinetic-slam" (dynamic high-retention slam) or "editorial-emphasis".
                 * Colors: Crisp White (#FFFFFF) text with warm Polished Gold (#FFD700) or Volt Yellow (#FFE600) highlights.
                 * Overlays: showTopOverlays MUST BE FALSE. No tacky top banners or floating boxes covering faces or disclaimers.
                 * Placement: Subtitles in lower-third safe zone (below chin, above lower edge).
               - Color Grading: Choose a style ('teal-orange', 'moody-dark', 'vibrant-pop', 'vintage-film'). 
                 * Select 'hdrBloom'=true if the scene has high-contrast practical lights or needs a cinematic glow.
               - USE EMOJIS & GRAPHICS. Ali Abdaal / MrBeast editing requires floating emojis for visual emphasis.
               - Color Grade LUT (Floor 5): Select a .cube 3D LUT name that best matches the visual environment and dialogue tone:
                 * 'intellectual_podcast' — subdued, lifted blacks, teal shadows, warm highlights
                 * 'philosophical_interview' — golden warmth, editorial lift
                 * 'business_podcast' — clean neutral-warm, flattering skin tones
                 * 'high_energy' — punchy contrast, saturated, warm
                 * 'moody_story' — teal-orange, crushed shadows
                 * 'scientific_breakdown' — clinical cool tones, blue shadows
                 * 'vibrant_pop' — highly saturated, warm, energetic
                 * 'vintage_film' — sepia, lifted blacks, desaturated
                 * 'clean_modern' — minimal grading, subtle contrast

            D. RETENTION EDITING (MRBEAST / ABDAAL TACTICS) (FLOORS 7, 9, 10):
               - EMOJIS: Generate 1-4 strategic `emojis` that pop up (e.g. 🤯, 📉, 💰) synced to high-impact moments. Use 'above-captions' or 'top-right'.
               - CAMERA MOVES & SHAKES: Schedule 1-3 dynamic `cameraMoves`. Use `scaleTarget` 1.15 to 1.3 for punch-ins. For huge emphasis, use `easing: spring`.
               - DATA VISUALIZATION: Scan the transcript for specific quantitative data (percentages, money, days/hours) for `dataVisualization`.
               - B-ROLL: Schedule 1 or 2 `brollCutaways` where an AI image will cover the screen for 2-3 seconds to break up the talking head.
               
            E. OUTPUT FORMAT:
            You MUST return a raw JSON object (and ONLY a JSON object) matching exactly this structure:
            {{
                "visualPerception": {{
                    "setting": "string",
                    "lightingMood": "string",
                    "subjectsAndEquipment": "string",
                    "hasNativeIntroOrDisclaimer": true/false,
                    "safeZoneRecommendation": "string"
                }},
                "conversationalAnalysis": {{
                    "primaryVibe": "string",
                    "intellectualDepth": "string",
                    "emotionalTone": "string",
                    "coreThesis": "string",
                    "keyDiscussionTopics": ["string", "string"]
                }},
                "artisticDirection": {{
                    "fontFamily": "editorial",
                    "fontRationale": "string",
                    "animation": "kinetic-slam",
                    "primaryTextColor": "#FFFFFF",
                    "highlightColor": "#FFD700",
                    "progressBarColor": "#FFD700",
                    "fontSize": 68,
                    "showTopOverlays": false,
                    "emphasisWords": ["word1", "word2"],
                    "colorGradingStyle": "teal-orange",
                    "colorGradeLUT": "intellectual_podcast",
                    "hdrBloom": false
                }},
                "directorSummary": "string",
                "dataVisualization": {{
                    "hasMetrics": true/false,
                    "metricValue": "string",
                    "metricLabel": "string",
                    "chartType": "counter-gauge",
                    "timestampStart": 0.0
                }},
                "filmTexture": {{
                    "enabled": true,
                    "grainOpacity": 0.08,
                    "vignetteOpacity": 0.2,
                    "textureType": "paper"
                }},
                "cameraMoves": [
                    {{
                        "timestampStart": 0.0,
                        "duration": 0.0,
                        "scaleTarget": 1.0,
                        "easing": "string"
                    }}
                ],
                "brollCutaways": [
                    {{
                        "timestampStart": 10.5,
                        "duration": 2.5,
                        "imagePrompt": "highly detailed cinematic shot of..."
                    }}
                ],
                "emojis": [
                    {{
                        "emoji": "🤯",
                        "startMs": 10500.0,
                        "durationMs": 1500.0,
                        "position": "above-captions",
                        "size": 110
                    }}
                ],
                "hookVariants": null
            }}
            """
            
            contents = keyframes + [prompt] if keyframes else [prompt]
            
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            raw_text = response.text
            if raw_text.startswith("```json"):
                raw_text = raw_text.replace("```json\n", "").replace("```", "").strip()
            raw_json = json.loads(raw_text)
            plan = AIDirectorPlan(**raw_json)
            
            print(f"[AI DIRECTOR] Multimodal AI Director Analysis Complete:")
            print(f"   - Vibe: '{plan.conversationalAnalysis.primaryVibe}' ({plan.conversationalAnalysis.intellectualDepth})")
            print(f"   - Visual Setting: '{plan.visualPerception.setting}' ({plan.visualPerception.lightingMood})")
            print(f"   - Native Intro Detected: {plan.visualPerception.hasNativeIntroOrDisclaimer}")
            print(f"   - Typography: '{plan.artisticDirection.fontFamily}' | Animation: '{plan.artisticDirection.animation}'")
            if plan.dataVisualization.hasMetrics:
                print(f"   - Data Found: {plan.dataVisualization.metricValue} {plan.dataVisualization.metricLabel} (Type: {plan.dataVisualization.chartType})")
            print(f"   - Core Thesis: \"{plan.conversationalAnalysis.coreThesis}\"")
        except Exception as e:
            print(f"[AI DIRECTOR] Gemini multimodal call error: {e}. Falling back to rule-based director...")
            plan = rule_based_fallback(full_text)
    else:
        print("[AI DIRECTOR] GEMINI_API_KEY/GOOGLE_API_KEY not found. Using rule-based director...")
        plan = rule_based_fallback(full_text)

    # Extract clean artistic attributes
    art = plan.artisticDirection
    emphasis_words = art.emphasisWords or []
    semantic_color_map = build_semantic_color_map(transcript, emphasis_words)
    highlight_col = art.highlightColor or "#FFD700"

    # Floor 5: Resolve the .cube LUT name
    color_grade_lut = getattr(art, "colorGradeLUT", None) or "intellectual_podcast"

    # Assemble pristine Remotion configuration props
    return {
        "vibe": plan.conversationalAnalysis.primaryVibe,
        "visualAtmosphere": plan.visualPerception.setting,
        "contentThemes": ", ".join(plan.conversationalAnalysis.keyDiscussionTopics),
        "coreThesis": plan.conversationalAnalysis.coreThesis,
        "reasoning": art.fontRationale,
        "subtitles": {
            "fontFamily": art.fontFamily or "editorial",
            "fontSize": max(66, min(int(art.fontSize or 68), 74)),
            "animation": art.animation or "kinetic-slam",
            "primaryTextColor": art.primaryTextColor or "#FFFFFF",
            "highlightColor": highlight_col,
            "semanticColors": semantic_color_map,
            "outlinePx": 8 if plan.visualPerception.setting.lower().find("bright") != -1 else 0
        },
        "hookVariants": plan.hookVariants,
        "hook": None,          # Removed: Strictly no starting box overlays clashing with video intro
        "focusBadge": None if plan.visualPerception.hasNativeIntroOrDisclaimer else {
            "text": plan.conversationalAnalysis.keyDiscussionTopics[0].upper() if plan.conversationalAnalysis.keyDiscussionTopics else "INSIGHT",
            "color": highlight_col
        },
        "progressBar": {
            "enabled": True,
            "position": "top",
            "height": 5,
            "color": art.progressBarColor or highlight_col,
            "backgroundColor": "rgba(0,0,0,0.30)",
            "glow": True
        },
        "colorGrading": {
            "enabled": True,
            "style": art.colorGradingStyle or "teal-orange",
            "hdrBloom": art.hdrBloom,
            "intensity": 0.6 if plan.visualPerception.lightingMood == "low_key_moody" else 0.4
        },
        "colorGradeLUT": color_grade_lut,  # Floor 5: .cube LUT name for FFmpeg post-pass
        "emojis": None,        # Removed: Strictly no cartoon stickers
        "filmTexture": {
            "enabled": True,
            "grainOpacity": 0.04 if plan.conversationalAnalysis.primaryVibe == "philosophical_interview" else 0.02,
            "vignetteIntensity": 0.6 if plan.visualPerception.lightingMood == "low_key_moody" else 0.3
        },
        "audioVisualizer": {
            "enabled": False
        },
        "dataVisualization": plan.dataVisualization.dict() if hasattr(plan, "dataVisualization") else None,
        "cameraMoves": [c.dict() if hasattr(c, "dict") else c for c in getattr(plan, "cameraMoves", [])],
        "brollCutaways": [b.dict() if hasattr(b, "dict") else b for b in getattr(plan, "brollCutaways", [])],
        "emphasisWords": emphasis_words,
        "directorPlan": plan.dict() if hasattr(plan, "dict") else plan
    }

def rule_based_fallback(text: str) -> AIDirectorPlan:
    """Smart heuristic director when Gemini API is unavailable."""
    text_lower = text.lower()
    
    if any(k in text_lower for k in ["body", "fasting", "health", "live", "age", "young", "food", "die", "life", "why"]):
        return AIDirectorPlan(
            visualPerception=VisualPerception(
                setting="Dark studio interview with podcast microphones and focused directional lighting",
                lightingMood="low_key_moody",
                subjectsAndEquipment="Two speakers, table setup, Shure SM7B microphones, native disclaimer intro",
                hasNativeIntroOrDisclaimer=True,
                safeZoneRecommendation="Lower-third placement (26% from bottom) to avoid faces, mics, and intro text"
            ),
            conversationalAnalysis=ConversationalAnalysis(
                primaryVibe="philosophical_interview",
                intellectualDepth="philosophical_reflective",
                emotionalTone="serious_and_contemplative",
                coreThesis="Exploring the biological philosophy and actionable mechanics of human longevity.",
                keyDiscussionTopics=["longevity", "fasting", "cellular health", "mortality", "discipline"]
            ),
            artisticDirection=ArtisticDirection(
                fontFamily="editorial",
                fontRationale="Montserrat and Playfair Display serif pairing conveys deep intellectual gravity without cluttering the frame.",
                animation="kinetic-slam",
                primaryTextColor="#FFFFFF",
                highlightColor="#FFD700",
                progressBarColor="#FFD700",
                fontSize=68,
                showTopOverlays=False,
                emphasisWords=["specifics", "live", "age", "body", "younger", "fasting", "food", "life", "years"],
                colorGradingStyle="teal-orange",
                hdrBloom=False
            ),
            dataVisualization=DataVisualization(
                hasMetrics=False,
                metricValue="",
                metricLabel="",
                chartType="none",
                timestampStart=0.0
            ),
            cameraMoves=[],
            brollCutaways=[
                BRollCutaway(timestampStart=5.0, duration=2.5, imagePrompt="cinematic dark moody shot of a glowing dna helix")
            ],
            directorSummary="Intellectual conversation about life and biology.",
            filmTexture=FilmTextureConfig(enabled=True, grainOpacity=0.08, vignetteOpacity=0.2, textureType="paper"),
            hookVariants=None
        )
    elif any(k in text_lower for k in ["business", "money", "dollar", "revenue", "founder", "market", "scale"]):
        return AIDirectorPlan(
            visualPerception=VisualPerception(
                setting="Modern executive studio setting",
                lightingMood="warm_cinematic",
                subjectsAndEquipment="Interviewer and founder, professional broadcast setup",
                hasNativeIntroOrDisclaimer=False,
                safeZoneRecommendation="Lower-third centered"
            ),
            conversationalAnalysis=ConversationalAnalysis(
                primaryVibe="business_podcast",
                intellectualDepth="tactical_educational",
                emotionalTone="revelatory",
                coreThesis="Strategic breakdown of venture scale and entrepreneurial economics.",
                keyDiscussionTopics=["business", "revenue", "market scale", "execution"]
            ),
            artisticDirection=ArtisticDirection(
                fontFamily="editorial",
                fontRationale="Editorial typography gives boardroom prestige.",
                animation="kinetic-slam",
                primaryTextColor="#FFFFFF",
                highlightColor="#FFD700",
                progressBarColor="#FFD700",
                fontSize=68,
                showTopOverlays=False,
                emphasisWords=["money", "business", "market", "revenue", "scale", "lesson"],
                colorGradingStyle="teal-orange",
                hdrBloom=False
            ),
            dataVisualization=DataVisualization(
                hasMetrics=False,
                metricValue="",
                metricLabel="",
                chartType="none",
                timestampStart=0.0
            ),
            cameraMoves=[],
            brollCutaways=[
                BRollCutaway(timestampStart=5.0, duration=2.5, imagePrompt="cinematic 4k shot of a modern skyscraper boardroom at night")
            ],
            directorSummary="High-credibility financial and entrepreneurial layout.",
            filmTexture=FilmTextureConfig(enabled=True, grainOpacity=0.08, vignetteOpacity=0.2, textureType="paper"),
            hookVariants=None
        )
    else:
        return AIDirectorPlan(
            visualPerception=VisualPerception(
                setting="Intimate dialogue setting with studio microphones",
                lightingMood="intimate_studio",
                subjectsAndEquipment="Speaker and host dialogue",
                hasNativeIntroOrDisclaimer=False,
                safeZoneRecommendation="Lower-third centered"
            ),
            conversationalAnalysis=ConversationalAnalysis(
                primaryVibe="philosophical_interview",
                intellectualDepth="philosophical_reflective",
                emotionalTone="reflective",
                coreThesis="Thought-provoking intellectual dialogue.",
                keyDiscussionTopics=["insight", "perspective", "growth"]
            ),
            artisticDirection=ArtisticDirection(
                fontFamily="editorial",
                fontRationale="Dignified modern editorial serif/sans balance.",
                animation="kinetic-slam",
                primaryTextColor="#FFFFFF",
                highlightColor="#FFD700",
                progressBarColor="#FFD700",
                fontSize=68,
                showTopOverlays=False,
                emphasisWords=["truth", "secret", "never", "always", "know", "how"],
                colorGradingStyle="teal-orange",
                hdrBloom=False
            ),
            dataVisualization=DataVisualization(
                hasMetrics=False,
                metricValue="",
                metricLabel="",
                chartType="none",
                timestampStart=0.0
            ),
            cameraMoves=[],
            brollCutaways=[],
            directorSummary="Clean intellectual dialogue short.",
            filmTexture=FilmTextureConfig(enabled=True, grainOpacity=0.08, vignetteOpacity=0.2, textureType="paper"),
            hookVariants=None
        )
