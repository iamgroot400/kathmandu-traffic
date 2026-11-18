#!/usr/bin/env python3
"""Place the 51 JICA 2011 small zones on the map: data/jica_od/zones_2011.csv.

Source: Figure 5.1.1 Zoning Map (JICA 2012 main report vol. 2, p. 5-4), rendered at
2000 px wide. Pixel positions of the zone-number labels and of village (VDC) name
labels were read off the rendered image by eye (shortcut: label position stands in for
the zone centroid, ~0.3-1 km off in large rural zones; digitise polygons if that matters).
Village labels are geocoded with OSM Nominatim and an affine pixel->lat/lon transform
is fitted by least squares; points with large residuals are dropped and reported.

    python scripts/georef_jica_zones.py
"""
import csv
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np

ROOT = Path(__file__).parent.parent
OUT = ROOT / "data" / "jica_od"
CACHE = OUT / "geocode_cache.json"

ZONE_PX = {  # zone label centre, display px of the 2000-px render
    "101": (706.5, 641.8), "102": (694.6, 615.3), "103": (716.4, 567.8), "104": (730.2, 633.9),
    "105": (801.5, 610.2), "106": (788.8, 676.7), "107": (738.1, 730.1), "108": (655.0, 713.1),
    "109": (630.5, 699.6), "110": (579.0, 710.3), "111": (603.5, 644.2), "112": (633.2, 588.4),
    "113": (635.2, 637.9), "114": (635.2, 673.5), "115": (659.0, 661.6), "116": (662.1, 580.9),
    "117": (674.0, 678.7), "118": (700.5, 683.4), "119": (769.8, 765.8),
    "201": (502, 805), "202": (558, 849),
    "301": (643.1, 752.7), "302": (623.3, 811.3), "303": (690, 858), "304": (725.5, 805.3),
    "305": (692.6, 795.4), "306": (672.0, 791.5),
    "401": (1083, 766), "402": (1090, 805), "403": (1021, 800), "404": (1043, 778),
    "501": (872, 760), "502": (848, 783),
    "601": (860, 683), "602": (986, 571), "603": (1208, 490), "604": (979, 416), "605": (773, 403),
    "606": (583, 396), "607": (456, 594), "608": (487, 708), "609": (342, 711), "610": (510, 893),
    "701": (618, 1005), "702": (731, 1045), "703": (886, 1090), "704": (851, 922),
    "801": (998, 883), "802": (1193, 773), "803": (1057, 686),
}
VILLAGE_PX = {
    "Thankot": (297, 731), "Sundarijal": (1036, 333), "Budhanilkantha": (797, 346),
    "Kapan": (825, 535), "Jorpati": (878, 585), "Gothatar": (865, 666), "Lubhu": (850, 935),
    "Godawari": (892, 1123), "Bungamati": (614, 990), "Chapagaun": (708, 1098),
    "Thecho": (678, 1008), "Changunarayan": (1058, 630), "Imadol": (760, 850),
    "Tikathali": (820, 859), "Siddhipur": (812, 898), "Harisiddhi": (761, 924),
    "Balkot": (864, 820), "Dadhikot": (955, 905), "Matatirtha": (372, 816),
    "Dhapasi": (711, 505), "Thaiba": (782, 992), "Khokana": (588, 920), "Sainbu": (627, 885),
    "Duwakot": (985, 706), "Lamatar": (940, 975), "Nayapati": (972, 478),
    "Gokarneshwor": (934, 548), "Mulpani": (936, 645), "Sitapaila": (520, 635),
    "Ramkot": (430, 618), "Dharmasthali": (601, 451), "Goldhunga": (546, 481),
    "Jitpurphedi": (537, 389), "Kabhresthali": (610, 337), "Chunikhel": (858, 474),
    "Baluwa": (908, 439), "Mahankal": (761, 494), "Nagarkot": (1290, 633),
    "Bageshwari": (1247, 692), "Sudal": (1216, 762), "Tathali": (1201, 812),
    "Chitapol": (1200, 870), "Nankhel": (1142, 902), "Sipadol": (1073, 895),
    "Gundu": (1016, 904), "Kautunje": (979, 828),
}
VALLEY = (85.15, 27.55, 85.60, 27.85)        # lon/lat box: reject geocodes outside the valley


def geocode(name, cache):
    if name not in cache:
        q = urllib.parse.urlencode({"q": f"{name}, Nepal", "format": "json", "limit": 5,
                                    "viewbox": ",".join(map(str, VALLEY)), "bounded": 1})
        req = urllib.request.Request(f"https://nominatim.openstreetmap.org/search?{q}",
                                     headers={"User-Agent": "research-traffic-model/0.1"})
        cache[name] = json.load(urllib.request.urlopen(req, timeout=30))
        time.sleep(1.1)                       # Nominatim usage policy: max 1 request/s
    hits = cache[name]
    return (float(hits[0]["lat"]), float(hits[0]["lon"])) if hits else None


def fit(px, ll):
    A = np.c_[px, np.ones(len(px))]
    coef, *_ = np.linalg.lstsq(A, ll, rcond=None)
    return coef, A @ coef


def km(a, b):
    return np.hypot((a[:, 0] - b[:, 0]) * 111.0, (a[:, 1] - b[:, 1]) * 111.0 * np.cos(np.radians(27.7)))


def main():
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    pts = []
    for name, p in VILLAGE_PX.items():
        g = geocode(name, cache)
        CACHE.write_text(json.dumps(cache, indent=1))
        if g is None:
            print(f"  not found: {name}")
        else:
            pts.append((name, p, g))
    names = [n for n, _, _ in pts]
    px = np.array([p for _, p, _ in pts], float)
    ll = np.array([g for _, _, g in pts], float)
    keep = np.ones(len(pts), bool)
    for _ in range(5):                        # drop geocodes > 2.5 km off the fitted map
        coef, pred = fit(px[keep], ll[keep])
        err = km(np.c_[px, np.ones(len(px))] @ coef, ll)
        new = err < 2.5
        if (new == keep).all():
            break
        keep = new
    for n, e, k in zip(names, err, keep):
        if not k:
            print(f"  dropped {n}: {e:.1f} km off")
    print(f"control points used: {keep.sum()}/{len(pts)}, "
          f"median residual {np.median(err[keep]):.2f} km, max {err[keep].max():.2f} km")
    # map scale bar: 2.5 km = 1735-1610 px; the fitted transform should agree
    kmpx = km(np.array([[0, 0]]) @ coef[:2] + coef[2], np.array([[125, 0]]) @ coef[:2] + coef[2])[0]
    print(f"fitted scale: 125 px = {kmpx:.2f} km (map scale bar says ~2.5 km)")
    with (OUT / "zones_2011.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["zone", "lat", "lon"])
        for z, p in sorted(ZONE_PX.items()):
            lat, lon = np.r_[p, 1.0] @ coef
            w.writerow([z, round(lat, 6), round(lon, 6)])
    print(f"wrote {OUT / 'zones_2011.csv'} ({len(ZONE_PX)} zones; 901 is outside the map)")


if __name__ == "__main__":
    main()
