#!/usr/bin/env python3
"""米国 物流施設（Industrial）売買取引量マップを PNG で出力"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon
from matplotlib.collections import PatchCollection
import matplotlib.font_manager as fm

# 日本語フォント
jp_font_path = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
jp_font = fm.FontProperties(fname=jp_font_path)

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

# US states GeoJSON 読み込み
geo = json.loads(Path("/tmp/us_states.json").read_text())

fig, ax = plt.subplots(figsize=(16, 10), dpi=140)

# 州ポリゴンを描画（アラスカ・ハワイ・プエルトリコは除外して本土のみ表示）
EXCLUDE = {"Alaska", "Hawaii", "Puerto Rico"}
patches = []
for feat in geo["features"]:
    name = feat["properties"]["name"]
    if name in EXCLUDE:
        continue
    geom = feat["geometry"]
    coords_list = geom["coordinates"]
    if geom["type"] == "Polygon":
        coords_list = [coords_list]
    for poly in coords_list:
        ring = poly[0]
        patches.append(MplPolygon(ring, closed=True))

pc = PatchCollection(patches, facecolor="#eef2f7", edgecolor="#94a3b8", linewidths=0.6)
ax.add_collection(pc)

# バブル（面積が取引量に比例）
max_vol = max(m[3] for m in markets)
# 面積 s (matplotlib scatter is area in points^2)
size_scale = 2400.0 / max_vol  # 最大バブルを s≈2400pt^2

lats = [m[1] for m in markets]
lons = [m[2] for m in markets]
vols = [m[3] for m in markets]
sizes = [v * size_scale for v in vols]

from matplotlib.colors import LinearSegmentedColormap
cmap = LinearSegmentedColormap.from_list(
    "ind", ["#60a5fa", "#2563eb", "#1e3a8a"]
)
sc = ax.scatter(
    lons, lats,
    s=sizes,
    c=vols,
    cmap=cmap,
    vmin=0, vmax=max_vol,
    alpha=0.85,
    edgecolor="#0b1f4d",
    linewidth=0.8,
    zorder=3,
)

# 上位5マーケットにラベル
top5 = sorted(markets, key=lambda m: -m[3])[:5]
for name, lat, lon, vol in top5:
    short = name.split(" / ")[0].split("–")[0]
    ax.annotate(
        f"{short}\n${vol:.1f}B",
        xy=(lon, lat),
        xytext=(0, -22),
        textcoords="offset points",
        ha="center", va="top",
        fontsize=9,
        color="#0f172a",
        fontproperties=jp_font,
        zorder=4,
    )

# カラーバー
cbar = plt.colorbar(sc, ax=ax, shrink=0.55, pad=0.01)
cbar.set_label("取引額 ($B)", fontproperties=jp_font, fontsize=11)

# 凡例（円サイズ）
legend_vols = [2, 5, 10]
for i, v in enumerate(legend_vols):
    ax.scatter([], [], s=v * size_scale, c="#3182bd", alpha=0.78,
               edgecolor="white", linewidth=1.0, label=f"${v}B")
leg = ax.legend(
    scatterpoints=1, frameon=True, labelspacing=1.6,
    title="取引額", loc="lower left", borderpad=1.0,
)
leg.get_title().set_fontproperties(jp_font)
for text in leg.get_texts():
    text.set_fontproperties(jp_font)

# 本土の表示範囲
ax.set_xlim(-125, -66)
ax.set_ylim(24, 50)
ax.set_aspect("auto")
ax.set_xticks([]); ax.set_yticks([])
for spine in ax.spines.values():
    spine.set_visible(False)

ax.set_title(
    "米国 物流施設（Industrial）売買取引量  ― 主要マーケット別年間取引額",
    fontproperties=jp_font, fontsize=15, pad=12,
)
fig.text(
    0.5, 0.03,
    "出典: MSCI Real Capital Analytics / CBRE / JLL 等の公開レポートに基づく代表値（概算）",
    ha="center", fontproperties=jp_font, fontsize=9, color="#555",
)

out = Path("/home/user/Claude/us_industrial_transactions_map.png")
plt.savefig(out, bbox_inches="tight", facecolor="white")
print(f"saved: {out}")
