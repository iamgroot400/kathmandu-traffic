#!/usr/bin/env python3
"""Count vehicles crossing lines in an intersection video, by class and 15-minute bin.

Each vehicle is detected (YOLO) and tracked (ByteTrack) from frame to frame, and is
counted once per line, at the moment its bottom-centre point crosses that line. Draw
one line across each approach, just before the stop line, so every entering vehicle
crosses exactly one of them. Entering volume = the sum over approach lines.

Run with the vision environment, not the simulation one:

    .venv-vision/Scripts/python.exe fieldcount/count_video.py snapshot video.mp4
        -> writes video_frame.png; open it and read off pixel coordinates for each line
    .venv-vision/Scripts/python.exe fieldcount/count_video.py count video.mp4 lines.json
        -> writes video_counts.csv (15-min bins) and video_check.mp4 (annotated, optional)

lines.json:
    {"start": "2026-11-20 09:00",
     "lines": {"north": [[410, 300], [700, 320]], "east": [[900, 380], [920, 620]]}}

Known limits: COCO has no class for tempos, e-rickshaws or microbuses; they are
counted as car, bus or truck, whichever the detector picks. Riders on motorcycles
are not counted separately (person detections are ignored). Check a few minutes of
the annotated video by hand against the CSV before trusting a site's numbers.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

VEHICLES = {1: "bicycle", 2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}   # COCO ids
BIN_S = 900


def side(p, a, b) -> float:
    """Signed area: which side of line a-b the point p lies on (0 = on the line)."""
    return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])


def crossed(p0, p1, a, b) -> bool:
    """True if the step p0 -> p1 crosses segment a-b (touching counts once, on arrival)."""
    s0, s1 = side(p0, a, b), side(p1, a, b)
    if s0 == 0 or (s0 > 0) == (s1 > 0) or s1 == 0 and s0 == 0:
        return False
    t0, t1 = side(a, p0, p1), side(b, p0, p1)
    return (t0 > 0) != (t1 > 0) or t0 == 0 or t1 == 0


# a vehicle moving straight through a vertical line counts; moving parallel, or
# stopping short, or crossing beyond the segment's end does not
assert crossed((0, 5), (10, 5), (5, 0), (5, 10))
assert not crossed((0, 5), (4, 5), (5, 0), (5, 10))
assert not crossed((0, 20), (10, 20), (5, 0), (5, 10))
assert not crossed((5, 1), (5, 9), (5, 0), (5, 10))


def snapshot(video: Path) -> None:
    import cv2
    cap = cv2.VideoCapture(str(video))
    ok, frame = cap.read()
    if not ok:
        raise SystemExit(f"could not read a frame from {video}")
    out = video.with_name(video.stem + "_frame.png")
    cv2.imwrite(str(out), frame)
    h, w = frame.shape[:2]
    print(f"wrote {out} ({w}x{h} px, {cap.get(cv2.CAP_PROP_FPS):.1f} fps, "
          f"{cap.get(cv2.CAP_PROP_FRAME_COUNT) / max(cap.get(cv2.CAP_PROP_FPS), 1) / 60:.1f} min)")


def count(video: Path, lines_file: Path, model: str, annotate: bool, stride: int) -> None:
    import cv2
    from ultralytics import YOLO

    cfg = json.loads(lines_file.read_text(encoding="utf-8"))
    lines = {k: (tuple(v[0]), tuple(v[1])) for k, v in cfg["lines"].items()}
    start = datetime.strptime(cfg["start"], "%Y-%m-%d %H:%M") if "start" in cfg else None

    cap = cv2.VideoCapture(str(video))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    writer = None
    if annotate:
        w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        writer = cv2.VideoWriter(str(video.with_name(video.stem + "_check.mp4")),
                                 cv2.VideoWriter_fourcc(*"mp4v"), fps / stride, (w, h))

    det = YOLO(model)
    last_pos, counted = {}, set()
    bins = defaultdict(int)                       # (bin, line, class) -> vehicles
    frame_no = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frame_no += 1
        if frame_no % stride:
            continue
        res = det.track(frame, persist=True, classes=list(VEHICLES), verbose=False,
                        tracker="bytetrack.yaml")[0]
        t_s = frame_no / fps
        if res.boxes.id is not None:
            for (x1, y1, x2, y2), tid, cls in zip(res.boxes.xyxy.tolist(), res.boxes.id.int().tolist(),
                                                  res.boxes.cls.int().tolist()):
                p = ((x1 + x2) / 2, y2)           # bottom centre: where the vehicle meets the road
                if tid in last_pos:
                    for name, (a, b) in lines.items():
                        if (tid, name) not in counted and crossed(last_pos[tid], p, a, b):
                            counted.add((tid, name))
                            bins[(int(t_s // BIN_S), name, VEHICLES[cls])] += 1
                last_pos[tid] = p
        if writer is not None:
            img = res.plot()
            for name, (a, b) in lines.items():
                cv2.line(img, tuple(map(int, a)), tuple(map(int, b)), (0, 255, 255), 2)
                n = sum(v for (_, ln, _), v in bins.items() if ln == name)
                cv2.putText(img, f"{name}: {n}", tuple(map(int, a)), cv2.FONT_HERSHEY_SIMPLEX, .8, (0, 255, 255), 2)
            writer.write(img)
        if frame_no % (stride * 500) == 0:
            print(f"  {frame_no / max(total, 1):.0%}  ({t_s / 60:.1f} min of video)", flush=True)
    cap.release()
    if writer is not None:
        writer.release()

    out = video.with_name(video.stem + "_counts.csv")
    classes = sorted(set(VEHICLES.values()))
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["bin_start", "line", *classes, "total"])
        for b in sorted({k[0] for k in bins}):
            label = (start + timedelta(seconds=b * BIN_S)).strftime("%H:%M") if start else f"{b * 15} min"
            for name in lines:
                row = [bins.get((b, name, c), 0) for c in classes]
                w.writerow([label, name, *row, sum(row)])
    grand = sum(bins.values())
    hours = frame_no / fps / 3600
    print(f"wrote {out}: {grand} vehicles over {hours * 60:.0f} min "
          f"({grand / hours:.0f} veh/h entering across all lines)" if hours else f"wrote {out}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Vehicle counts from intersection video")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("snapshot"); s.add_argument("video", type=Path)
    c = sub.add_parser("count")
    c.add_argument("video", type=Path); c.add_argument("lines", type=Path)
    c.add_argument("--model", default="yolov8n.pt", help="larger is more accurate and slower, e.g. yolov8s.pt")
    c.add_argument("--stride", type=int, default=2, help="process every Nth frame (2 at 25-30 fps is enough to track)")
    c.add_argument("--annotate", action="store_true", help="also write <video>_check.mp4 for hand checking")
    a = ap.parse_args()
    if a.cmd == "snapshot":
        snapshot(a.video)
    else:
        count(a.video, a.lines, a.model, a.annotate, a.stride)


if __name__ == "__main__":
    main()
