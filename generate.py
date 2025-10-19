import requests
import pandas as pd
import json
import time
from urllib.parse import urlparse, unquote, quote
from datetime import datetime, timedelta,timezone

HEADERS = {
    "User-Agent": "WikiViewBot/1.0 (your.email@example.com)"
}

# グループAとBのWikipedia記事URL一覧（手動定義）
group_a = {
    "乃木坂46": {
        "ja": "https://ja.wikipedia.org/wiki/乃木坂46",
        "en": "https://en.wikipedia.org/wiki/Nogizaka46"
    },
    "AKB48": {
        "ja": "https://ja.wikipedia.org/wiki/AKB48",
        "en": "https://en.wikipedia.org/wiki/AKB48"
    },
    "僕が見たかった青空": {
        "ja": "https://ja.wikipedia.org/wiki/僕が見たかった青空",
        "en": "https://en.wikipedia.org/wiki/Boku_ga_Mitakatta_Aozora"
    },
    "NiziU": {
        "ja": "https://ja.wikipedia.org/wiki/NiziU",
        "en": "https://en.wikipedia.org/wiki/NiziU"
    },
    "ME:I": {
        "ja": "https://ja.wikipedia.org/wiki/ME:I",
        "en": "https://en.wikipedia.org/wiki/ME:I"
    }
}

group_b = {
    "ILLIT": {
        "ja": "https://ja.wikipedia.org/wiki/ILLIT",
        "en": "https://en.wikipedia.org/wiki/Illit"
    },
    "ルセラフィム": {
        "ja": "https://ja.wikipedia.org/wiki/LE_SSERAFIM",
        "en": "https://en.wikipedia.org/wiki/Le_Sserafim"
    },
    "NewJeans": {
        "ja": "https://ja.wikipedia.org/wiki/NewJeans",
        "en": "https://en.wikipedia.org/wiki/NewJeans"
    },
    "Kep1er": {
        "ja": "https://ja.wikipedia.org/wiki/Kep1er",
        "en": "https://en.wikipedia.org/wiki/Kep1er"
    },
    "IVE": {
        "ja": "https://ja.wikipedia.org/wiki/IVE_(%E9%9F%B3%E6%A5%BD%E3%82%B0%E3%83%AB%E3%83%BC%E3%83%97)",
        "en": "https://en.wikipedia.org/wiki/Ive_(group)"
    }
}

# URLから記事タイトルを抽出してAPI用にエンコード
def extract_title_from_url(url):
    path = urlparse(url).path
    title = path.split("/wiki/")[-1]
    return quote(unquote(title))

# APIから閲覧数を取得（リクエスト間に待機時間あり）
def get_views(project, url, start, end):
    title = extract_title_from_url(url)
    start_str = start.strftime('%Y%m%d')
    end_str = end.strftime('%Y%m%d')
    api = f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/{project}/all-access/all-agents/{title}/daily/{start_str}/{end_str}"
    time.sleep(0.5)
    r = requests.get(api, headers=HEADERS)
    
    if r.status_code == 200:
        data = r.json()
        if not data["items"]:
            print(f"閲覧数ゼロ: {title} ({project}) → {start_str}〜{end_str}")
            return 0
        return sum(item["views"] for item in data["items"])
    else:
        print(f"取得失敗: {title} ({project}) → {r.status_code}")
        return 0

# グループごとのランキング表を作成
def build_table(group, start, end):
    rows = []
    for name, urls in group.items():
        ja_views = get_views("ja.wikipedia.org", urls["ja"], start, end)
        en_views = get_views("en.wikipedia.org", urls["en"], start, end)
        rows.append({
            "name": name,
            "ja_views": ja_views,
            "en_views": en_views
        })
    df = pd.DataFrame(rows)
    return df.sort_values(by="ja_views", ascending=False).reset_index(drop=True)

# 日付ラベルを生成
def format_date_range(start, end):
    def format(d):
        weekday = "月火水木金土日"[d.weekday()]
        return f"{d.year}年{d.month}月{d.day}日（{weekday}）"
    return {
        "start": format(start),
        "end": format(end)
    }

# 一昨日を基準に各期間を取得
date_labels = {}
JST = timezone(timedelta(hours=9))
base_end = datetime.now(JST).date() - timedelta(days=2)

for days in [1, 7, 30]:
    end = base_end
    start = end - timedelta(days=days - 1)

    df_a = build_table(group_a, start, end)
    df_b = build_table(group_b, start, end)

    df_a.to_csv(f"groupA_{days}days.csv", index=False)
    df_b.to_csv(f"groupB_{days}days.csv", index=False)

    date_labels[days] = format_date_range(start, end)

JST = timezone(timedelta(hours=9))
last_updated = datetime.now(JST).strftime("%Y年%m月%d日 %H:%M:%S")

# 日付ラベルを保存
with open("date_labels.json", "w", encoding="utf-8") as f:
    json.dump(date_labels, f, ensure_ascii=False, indent=2)

# 更新日時を保存（統一された変数を使用）
with open("last_updated.txt", "w", encoding="utf-8") as f:
    f.write(last_updated)

