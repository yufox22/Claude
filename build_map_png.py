#!/usr/bin/env python3
"""米国 物流施設（Industrial）売買取引量マップを PNG で出力
   - 州境、主要Interstate（Major Highway）、鉄道網を背景に重ねる
   - 主要マーケットの年間取引額を円サイズで表現
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon
from matplotlib.collections import PatchCollection, LineCollection
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D
import matplotlib.font_manager as fm

# 日本語フォント
jp_font = fm.FontProperties(fname="/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf")

# 主要米国産業用不動産マーケット（年間取引額 $B, MSCI/RCA・CBRE・JLL 等の公開資料より）
markets = [
    ("Los Angeles / Inland Empire", 34.05, -117.75, 12.0),
    ("Northern New Jersey",         40.74,  -74.17,  7.5),
    ("Dallas–Fort Worth",           32.78,  -96.80,  7.2),
    ("Chicago",                     41.85,  -87.65,  6.1),
    ("Atlanta",                     33.75,  -84.39,  5.0),
    ("Phoenix",                     33.45, -112.07,  4.5),
    ("Pennsylvania I-78/I-81",      40.63,  -75.60,  4.0),
    ("Houston",                     29.76,  -95.37,  3.6),
    ("Seattle",                     47.61, -122.33,  3.1),
    ("South Florida (Miami)",       25.77,  -80.19,  3.0),
    ("SF Bay Area / Oakland",       37.80, -122.27,  2.6),
    ("Indianapolis",                39.77,  -86.16,  2.5),
    ("Columbus",                    39.96,  -82.99,  2.4),
    ("Nashville",                   36.16,  -86.78,  2.0),
    ("Memphis",                     35.15,  -90.05,  1.8),
    ("Kansas City",                 39.10,  -94.58,  1.8),
    ("Denver",                      39.74, -104.99,  1.7),
    ("Boston",                      42.36,  -71.06,  1.6),
    ("Charlotte",                   35.23,  -80.84,  1.5),
    ("Baltimore",                   39.29,  -76.61,  1.5),
    ("Minneapolis",                 44.98,  -93.27,  1.3),
    ("Cincinnati",                  39.10,  -84.51,  1.2),
    ("Las Vegas",                   36.17, -115.14,  1.2),
    ("Portland",                    45.52, -122.68,  1.1),
    ("Orlando",                     28.54,  -81.38,  1.0),
    ("Tampa",                       27.95,  -82.46,  1.0),
    ("Salt Lake City",              40.76, -111.89,  1.0),
    ("Austin",                      30.27,  -97.74,  0.9),
    ("Reno",                        39.53, -119.81,  0.8),
    ("San Antonio",                 29.42,  -98.49,  0.7),
]

# 本土 bbox
BBOX = (-125, 24, -66, 50)  # west, south, east, north

def in_bbox(lon, lat):
    return BBOX[0] <= lon <= BBOX[2] and BBOX[1] <= lat <= BBOX[3]

def line_in_bbox(coords):
    return any(in_bbox(x, y) for x, y in coords)

# --- 州ポリゴン ---
geo = json.loads(Path("/tmp/us_states.json").read_text())
EXCLUDE = {"Alaska", "Hawaii", "Puerto Rico"}
state_patches = []
for feat in geo["features"]:
    if feat["properties"]["name"] in EXCLUDE:
        continue
    g = feat["geometry"]
    polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
    for poly in polys:
        state_patches.append(MplPolygon(poly[0], closed=True))

# --- 鉄道（Natural Earth, 北米→US bbox フィルタ）---
rail = json.loads(Path("/tmp/ne_rail.json").read_text())
rail_segments = []
for f in rail["features"]:
    if f["properties"].get("continent") != "North America":
        continue
    g = f["geometry"]
    lines = g["coordinates"] if g["type"] == "MultiLineString" else [g["coordinates"]]
    for line in lines:
        if line_in_bbox(line):
            rail_segments.append(line)

# --- 主要高速道路（Interstate 相当: 'Major Highway' かつ US） ---
roads = json.loads(Path("/tmp/ne_roads.json").read_text())
hwy_segments = []
for f in roads["features"]:
    p = f["properties"]
    if p.get("sov_a3") != "USA":
        continue
    if p.get("type") != "Major Highway":
        continue
    g = f["geometry"]
    lines = g["coordinates"] if g["type"] == "MultiLineString" else [g["coordinates"]]
    for line in lines:
        if line_in_bbox(line):
            hwy_segments.append(line)

# --- 描画 ---
fig, ax = plt.subplots(figsize=(16, 10), dpi=140)

# 州
pc = PatchCollection(state_patches, facecolor="#f1f4f9",
                     edgecolor="#94a3b8", linewidths=0.6, zorder=1)
ax.add_collection(pc)

# 鉄道（薄い灰色、細線）
rail_lc = LineCollection(rail_segments, colors="#6b7280",
                         linewidths=0.35, alpha=0.55, zorder=2)
ax.add_collection(rail_lc)

# 高速道路（オレンジ系、やや太線）
hwy_lc = LineCollection(hwy_segments, colors="#ef6c00",
                        linewidths=0.9, alpha=0.85, zorder=3)
ax.add_collection(hwy_lc)

# バブル（取引額）
max_vol = max(m[3] for m in markets)
size_scale = 2400.0 / max_vol
cmap = LinearSegmentedColormap.from_list("ind", ["#60a5fa", "#2563eb", "#1e3a8a"])

lats = [m[1] for m in markets]
lons = [m[2] for m in markets]
vols = [m[3] for m in markets]
sizes = [v * size_scale for v in vols]

sc = ax.scatter(lons, lats, s=sizes, c=vols, cmap=cmap,
                vmin=0, vmax=max_vol, alpha=0.88,
                edgecolor="#0b1f4d", linewidth=0.9, zorder=5)

# 上位5マーケットのラベル
top5 = sorted(markets, key=lambda m: -m[3])[:5]
for name, lat, lon, vol in top5:
    short = name.split(" / ")[0].split("–")[0]
    ax.annotate(
        f"{short}\n${vol:.1f}B",
        xy=(lon, lat), xytext=(0, -24), textcoords="offset points",
        ha="center", va="top", fontsize=9, color="#0f172a",
        fontproperties=jp_font, zorder=6,
        bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.7),
    )

# カラーバー（取引額）
cbar = plt.colorbar(sc, ax=ax, shrink=0.55, pad=0.01)
cbar.set_label("取引額 ($B)", fontproperties=jp_font, fontsize=11)

# 凡例 1: バブルサイズ
bubble_handles = [
    plt.scatter([], [], s=v * size_scale, c="#2563eb",
                edgecolor="#0b1f4d", linewidth=0.8, alpha=0.85, label=f"${v}B")
    for v in (2, 5, 10)
]
# 凡例 2: 線種
line_handles = [
    Line2D([0], [0], color="#ef6c00", lw=2.0, label="主要高速道路 (Interstate)"),
    Line2D([0], [0], color="#6b7280", lw=1.2, alpha=0.7, label="鉄道網"),
]

leg1 = ax.legend(handles=bubble_handles, title="取引額",
                 loc="lower left", labelspacing=1.6, borderpad=1.0, frameon=True)
leg1.get_title().set_fontproperties(jp_font)
for t in leg1.get_texts(): t.set_fontproperties(jp_font)
ax.add_artist(leg1)

leg2 = ax.legend(handles=line_handles, title="インフラ",
                 loc="lower right", frameon=True)
leg2.get_title().set_fontproperties(jp_font)
for t in leg2.get_texts(): t.set_fontproperties(jp_font)

# 表示範囲
ax.set_xlim(BBOX[0], BBOX[2])
ax.set_ylim(BBOX[1], BBOX[3])
ax.set_aspect("auto")
ax.set_xticks([]); ax.set_yticks([])
for sp in ax.spines.values(): sp.set_visible(False)

ax.set_title(
    "米国 物流施設（Industrial）売買取引量  ×  主要インフラ（Interstate ／ 鉄道網）",
    fontproperties=jp_font, fontsize=15, pad=12,
)
fig.text(
    0.5, 0.03,
    "出典: 取引量=MSCI/RCA・CBRE・JLL 等の公開レポート代表値（概算）／ インフラ=Natural Earth 1:10m",
    ha="center", fontproperties=jp_font, fontsize=9, color="#555",
)

out = Path("/home/user/Claude/us_industrial_transactions_map.png")
plt.savefig(out, bbox_inches="tight", facecolor="white")
print(f"saved: {out}  rail={len(rail_segments)} hwy={len(hwy_segments)}")
