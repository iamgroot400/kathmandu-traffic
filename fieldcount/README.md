# Field counts: filming guide

Goal: 2026 peak-hour entering volumes at intersections JICA counted in 2011-12, so the
model can be checked against current traffic and the 14-year change can be measured.

## Where and when

| Priority | Intersection | JICA 2011-12 entering volume (veh/h, AM/PM avg) |
|---|---|---|
| 1 | Koteshwor | 9,928 |
| 2 | Kalanki | 8,884 |
| 3 | Thapathali | 16,328 |
| 4 | Chabahil | 9,204 |
| 5 | New Baneshwor | 15,424 |

- **9:00 to 10:00 am on a weekday** (Sunday to Thursday), the same hour JICA counted. Film a
  few minutes either side and note the exact start time.
- Avoid festival days, bandhs, VIP movements and heavy rain. Write down anything unusual.

## How to film

- **Height matters most.** A footbridge, rooftop or upper-floor window, looking down at the
  junction. From street level, vehicles hide each other and counts come out low.
- Landscape, phone on a support (railing, small tripod, taped to a bottle). No handheld: a
  moving camera breaks the counting lines.
- **See every approach**, or film from two spots at the same time and count each separately.
- 1080p is enough. Turn off auto-rotate and keep the phone plugged in or carry a power bank:
  an hour of video is about 6-8 GB at 1080p.

## Counting

```bash
.venv-vision/Scripts/python.exe fieldcount/count_video.py snapshot koteshwor.mp4
```

Open `koteshwor_frame.png`, and for each approach note two pixel points across the lanes just
before the stop line (any image viewer shows pixel coordinates). Write them to a file:

```json
{"start": "2026-11-20 09:00",
 "lines": {"from_bhaktapur": [[812, 420], [1100, 455]], "from_tinkune": [[300, 610], [520, 700]]}}
```

```bash
.venv-vision/Scripts/python.exe fieldcount/count_video.py count koteshwor.mp4 lines.json --annotate
```

Output: `koteshwor_counts.csv`, vehicles per approach, per vehicle class, per 15 minutes.
`--annotate` also writes a video with the boxes and lines drawn, so you can check it.

**Always hand-check one 5-minute stretch** of one approach against the CSV. If the counter is
more than about 10% off, use a larger model (`--model yolov8s.pt`) or a better camera spot.

## Known limits

- Tempos, e-rickshaws and microbuses are not separate classes; they are counted as car,
  bus or truck.
- Very dense motorcycle clusters can merge into one box. The hand check shows how much this
  matters at each site.
