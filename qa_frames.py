import os
import json
import hashlib
import subprocess
import cv2
import numpy as np

MANIFEST_PATH = "output/render_manifest.json"
PROPS_PATH = "remotion/props.json"
QA_DIR = "output/qa_frames"

_POSE_MODEL = None

def get_pose_model():
    global _POSE_MODEL
    if _POSE_MODEL is None:
        from ultralytics import YOLO
        _POSE_MODEL = YOLO("yolov8n-pose.pt")
    return _POSE_MODEL

def detect_face_box(frame, W, H):
    """
    Detects face box using YOLO pose keypoints (nose, eyes, ears)
    and expands slightly to include forehead and chin.
    Returns [x1, y1, x2, y2] in pixel coords, or None.
    """
    try:
        model = get_pose_model()
        results = model(frame, verbose=False)
        for r in results:
            if r.keypoints is not None and len(r.keypoints.xy) > 0:
                kpts = r.keypoints.xy[0].cpu().numpy()
                face_kpts = kpts[:5]
                valid = face_kpts[face_kpts.sum(axis=1) > 0]
                if len(valid) > 0:
                    fx1, fy1 = valid.min(axis=0)
                    fx2, fy2 = valid.max(axis=0)
                    fw, fh = fx2 - fx1, fy2 - fy1
                    hx1 = max(0, fx1 - fw * 0.25)
                    hy1 = max(0, fy1 - fh * 0.5)
                    hx2 = min(W, fx2 + fw * 0.25)
                    hy2 = min(H, fy2 + fh * 0.55)
                    return [int(hx1), int(hy1), int(hx2), int(hy2)]
    except Exception as e:
        print(f"  Warning: Face detection error: {e}")
    return None

def compute_rect_intersection(r1, r2):
    """Returns True, area if two [x1, y1, x2, y2] rects intersect, else False, 0"""
    ix1 = max(r1[0], r2[0])
    iy1 = max(r1[1], r2[1])
    ix2 = min(r1[2], r2[2])
    iy2 = min(r1[3], r2[3])
    if ix1 < ix2 and iy1 < iy2:
        return True, (ix2 - ix1) * (iy2 - iy1)
    return False, 0

def get_overlay_box(overlay_type, config, W, H):
    """
    Returns the expected bounding box [x1, y1, x2, y2] for an overlay.
    """
    if overlay_type == "hook":
        # Hook is top-centered (top: 5%, height ~5.5%, width ~48% for 24 chars at size S)
        scale = 0.85 if config.get("size") == "S" else (1.2 if config.get("size") == "L" else 1.0)
        box_w = int(min(0.70, 0.48 * scale) * W)
        box_h = int(0.055 * scale * H)
        x1 = (W - box_w) // 2
        y1 = int(0.048 * H)
        return [x1, y1, x1 + box_w, y1 + box_h]
    elif overlay_type == "badge":
        pos = config.get("position", "top-left")
        if pos == "top-left":
            return [int(0.08 * W), int(0.02 * H), int(0.48 * W), int(0.075 * H)]
        elif pos == "top-right":
            return [int(0.52 * W), int(0.02 * H), int(0.92 * W), int(0.075 * H)]
        else:
            return [int(0.25 * W), int(0.02 * H), int(0.75 * W), int(0.075 * H)]
    elif overlay_type == "card":
        card_pos = config.get("cardPosition", "center")
        if card_pos == "center-left":
            # left: 7%, top: 43.5%, width: 43%, height: ~10.5%
            return [int(0.07 * W), int(0.435 * H), int(0.50 * W), int(0.54 * H)]
        elif card_pos == "center-right":
            return [int(0.50 * W), int(0.435 * H), int(0.93 * W), int(0.54 * H)]
        elif card_pos == "lower-left":
            return [int(0.07 * W), int(0.56 * H), int(0.50 * W), int(0.665 * H)]
        elif card_pos == "lower-right":
            return [int(0.50 * W), int(0.56 * H), int(0.93 * W), int(0.665 * H)]
        else:
            # Legacy center card
            return [int(0.10 * W), int(0.38 * H), int(0.90 * W), int(0.50 * H)]
    return [0, 0, 0, 0]

def run_qa():
    print("\n" + "=" * 65)
    print("  VISUAL QA INSPECTION ENGINE (FLOOR 4)")
    print("=" * 65)

    if not os.path.exists(MANIFEST_PATH):
        raise ValueError("QA FAILED: render_manifest.json not found")

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    winner_file = manifest["videoPath"]
    if not os.path.exists(winner_file):
        raise ValueError(f"QA FAILED: Video {winner_file} not found")

    # Check modification time
    if os.path.getmtime(winner_file) < os.path.getmtime(PROPS_PATH):
        raise ValueError("QA FAILED: Final MP4 modification time is older than props.json")

    # Check hash
    with open(PROPS_PATH, "rb") as f:
        current_hash = hashlib.sha256(f.read()).hexdigest()

    if current_hash != manifest["propsSha256"]:
        raise ValueError("QA FAILED: Manifest props hash does not equal current props hash")

    with open(PROPS_PATH, "r", encoding="utf-8") as f:
        props = json.load(f)

    os.makedirs(QA_DIR, exist_ok=True)

    # Probe video dimensions
    cap = cv2.VideoCapture(winner_file)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 1080)
    H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 1920)
    cap.release()

    # Define standard safe zones (TikTok / Reels / Shorts UI standards)
    caption_safe_zone = [int(0.10 * W), int(0.70 * H), int(0.90 * W), int(0.88 * H)]
    platform_ui_right = [int(0.88 * W), int(0.35 * H), W, int(0.82 * H)]
    platform_ui_bottom = [0, int(0.82 * H), W, H]
    platform_ui_top = [0, 0, W, int(0.035 * H)]

    # Collect overlays and their 4 inspection timestamps:
    # 1. start + 0.0s
    # 2. start + 0.5s
    # 3. midpoint
    # 4. end - 0.25s
    overlays_to_test = []

    # Hook
    hook = props.get("hook")
    if hook:
        h_dur = hook.get("displayDurationSec", 2.5)
        overlays_to_test.append({
            "type": "hook",
            "name": f"Hook: '{hook.get('text')}'",
            "start": 0.0,
            "duration": h_dur,
            "config": hook
        })

    # Badge
    badge = props.get("focusBadge")
    if badge and badge.get("enabled", True):
        b_start = badge.get("startMs", 0) / 1000.0
        b_dur = badge.get("durationMs", 2500) / 1000.0
        overlays_to_test.append({
            "type": badge.get("variant", "badge"),
            "name": f"FocusBadge: '{badge.get('text')}'",
            "start": b_start,
            "duration": b_dur,
            "config": badge
        })

    # Takeaway cards / focusBadges
    badges = props.get("focusBadges", [])
    for idx, fb in enumerate(badges):
        if fb.get("enabled", True):
            fb_start = fb.get("startMs", 0) / 1000.0
            fb_dur = fb.get("durationMs", 1500) / 1000.0
            fb_type = fb.get("variant", "card")
            overlays_to_test.append({
                "type": fb_type,
                "name": f"focusBadges[{idx}] ({fb_type}): '{fb.get('text')}'",
                "start": fb_start,
                "duration": fb_dur,
                "config": fb
            })

    print(f"Found {len(overlays_to_test)} animated overlays for 4-point visual QA inspection.")

    all_qa_records = []
    qa_failures = []
    takeaway_card_records = []

    for item in overlays_to_test:
        start = item["start"]
        dur = item["duration"]
        item_type = item["type"]
        item_name = item["name"]
        item_cfg = item["config"]

        t_0 = round(start + 0.0, 3)
        t_05 = round(start + 0.5, 3)
        t_mid = round(start + dur / 2.0, 3)
        t_end = round(start + dur - 0.25, 3)

        sample_points = [
            ("start+0.0s (entrance)", t_0, False),  # False = entrance frame (low opacity)
            ("start+0.5s (full)", t_05, True),      # True = opaque frame
            ("midpoint", t_mid, True),               # True = opaque frame
            ("end-0.25s (pre-exit)", t_end, True),  # True = opaque frame
        ]

        print(f"\n--- Inspecting {item_name} ---")
        overlay_box = get_overlay_box(item_type, item_cfg, W, H)
        print(f"  Overlay Bounds: [{overlay_box[0]}, {overlay_box[1]}, {overlay_box[2]}, {overlay_box[3]}] "
              f"({overlay_box[0]/W*100:.1f}%, {overlay_box[1]/H*100:.1f}%, {overlay_box[2]/W*100:.1f}%, {overlay_box[3]/H*100:.1f}%)")

        for label, t, is_opaque_frame in sample_points:
            out_file = os.path.join(QA_DIR, f"qa_{item_type}_{t:.2f}s.png")
            cmd = ["ffmpeg", "-y", "-ss", str(t), "-i", winner_file, "-frames:v", "1", "-q:v", "2", out_file]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            frame = cv2.imread(out_file)
            if frame is None:
                qa_failures.append(f"Could not extract frame at {t}s for {item_name}")
                continue

            face_box = detect_face_box(frame, W, H)
            if face_box is None:
                # Default approximate head box if face undetectable
                face_box = [int(0.40 * W), int(0.20 * H), int(0.95 * W), int(0.35 * H)]

            pad_x = int(0.08 * W)
            pad_y = int(0.08 * H)
            padded_face = [
                max(0, face_box[0] - pad_x),
                max(0, face_box[1] - pad_y),
                min(W, face_box[2] + pad_x),
                min(H, face_box[3] + pad_y)
            ]

            # Intersection checks
            face_hit, face_overlap_area = compute_rect_intersection(overlay_box, padded_face)
            caption_hit, cap_overlap_area = compute_rect_intersection(overlay_box, caption_safe_zone)
            ui_right_hit, ui_right_area = compute_rect_intersection(overlay_box, platform_ui_right)
            ui_bottom_hit, ui_bottom_area = compute_rect_intersection(overlay_box, platform_ui_bottom)
            ui_top_hit, ui_top_area = compute_rect_intersection(overlay_box, platform_ui_top)

            # Draw annotated frame for visual inspection
            annotated = frame.copy()
            # Face box (Green)
            cv2.rectangle(annotated, (face_box[0], face_box[1]), (face_box[2], face_box[3]), (0, 255, 0), 3)
            cv2.putText(annotated, "FACE BOX", (face_box[0] + 5, face_box[1] - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            # Padded exclusion zone (Cyan)
            cv2.rectangle(annotated, (padded_face[0], padded_face[1]), (padded_face[2], padded_face[3]), (255, 255, 0), 2)
            cv2.putText(annotated, "FACE + 8% EXCLUSION", (padded_face[0] + 5, padded_face[1] - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 0), 2)
            # Overlay box (Magenta)
            cv2.rectangle(annotated, (overlay_box[0], overlay_box[1]), (overlay_box[2], overlay_box[3]), (255, 0, 255), 3)
            cv2.putText(annotated, f"OVERLAY: {item_type.upper()}", (overlay_box[0] + 5, overlay_box[1] - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2)
            # Subtitle zone (Yellow)
            cv2.rectangle(annotated, (caption_safe_zone[0], caption_safe_zone[1]),
                          (caption_safe_zone[2], caption_safe_zone[3]), (0, 255, 255), 2)
            cv2.putText(annotated, "SUBTITLE ZONE", (caption_safe_zone[0] + 5, caption_safe_zone[1] - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

            annotated_path = os.path.join(QA_DIR, f"annotated_{item_type}_{t:.2f}s.png")
            cv2.imwrite(annotated_path, annotated)

            record = {
                "item": item_name,
                "type": item_type,
                "timestamp": t,
                "sampling_point": label,
                "is_opaque_frame": is_opaque_frame,
                "frame_path": out_file,
                "annotated_path": annotated_path,
                "detected_face_box": {
                    "pixel": face_box,
                    "normalized": [round(face_box[0]/W, 3), round(face_box[1]/H, 3), round(face_box[2]/W, 3), round(face_box[3]/H, 3)]
                },
                "padded_face_box": {
                    "pixel": padded_face,
                    "normalized": [round(padded_face[0]/W, 3), round(padded_face[1]/H, 3), round(padded_face[2]/W, 3), round(padded_face[3]/H, 3)]
                },
                "overlay_region": {
                    "pixel": overlay_box,
                    "normalized": [round(overlay_box[0]/W, 3), round(overlay_box[1]/H, 3), round(overlay_box[2]/W, 3), round(overlay_box[3]/H, 3)]
                },
                "intersections": {
                    "face_padded": {"hit": face_hit, "area_px": face_overlap_area},
                    "captions": {"hit": caption_hit, "area_px": cap_overlap_area},
                    "platform_ui": {"hit": ui_right_hit or ui_bottom_hit or ui_top_hit,
                                    "right": ui_right_area, "bottom": ui_bottom_area, "top": ui_top_area}
                }
            }

            all_qa_records.append(record)
            if item_type == "card":
                takeaway_card_records.append(record)

            status_glyph = "✅"
            # Rule: Fail if any OPAQUE portion intersects face+8%, captions, or platform UI
            if is_opaque_frame:
                if face_hit:
                    status_glyph = "❌"
                    qa_failures.append(f"[{item_name} @ {t}s ({label})] Opaque overlay intersects Face + 8% padding (overlap={face_overlap_area} px^2)")
                if caption_hit:
                    status_glyph = "❌"
                    qa_failures.append(f"[{item_name} @ {t}s ({label})] Opaque overlay intersects Subtitle safe zone (overlap={cap_overlap_area} px^2)")
                if ui_right_hit or ui_bottom_hit:
                    status_glyph = "❌"
                    qa_failures.append(f"[{item_name} @ {t}s ({label})] Opaque overlay intersects Platform UI margins")
            else:
                if face_hit:
                    status_glyph = "⚠️"
                    print(f"  Note: Entrance frame at {t}s intersects geometric face zone, but opacity is ramping up.")

            print(f"  {status_glyph} {label} ({t:.2f}s): Face overlap: {face_overlap_area} px^2 | Captions overlap: {cap_overlap_area} px^2")

    print("\n" + "=" * 65)
    print("  QA RESULT SUMMARY")
    print("=" * 65)

    final_status = "passed"
    if qa_failures:
        final_status = "failed"
        print(f"❌ Visual QA FAILED with {len(qa_failures)} violation(s):")
        for err in qa_failures:
            print(f"   • {err}")
    else:
        print("✅ Visual QA PASSED: All animated overlays clear Face + 8% padding, Captions, and Platform UI!")

    # Update render manifest with exhaustive QA metrics
    manifest["visual_qa_status"] = final_status
    manifest["visual_qa_details"] = {
        "status": final_status,
        "failures": qa_failures,
        "takeaway_card_inspection": takeaway_card_records,
        "all_inspections_count": len(all_qa_records)
    }

    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"Manifest updated with visual_qa_status='{final_status}'.")

    if final_status == "failed":
        raise ValueError(f"QA FAILED: Visual overlays intersect critical safe zones: {qa_failures}")

if __name__ == "__main__":
    run_qa()
