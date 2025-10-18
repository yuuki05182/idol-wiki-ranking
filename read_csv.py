import pandas as pd
import json
from jinja2 import Template
from datetime import datetime, timedelta, timezone

# CSV読み込み関数
def load_csv(group, days):
    return pd.read_csv(f"{group}_{days}days.csv")

# 日数に応じた色分けクラス名を返す関数
def get_day_class(days):
    return {
        1: "day-1",
        7: "day-7",
        30: "day-30"
    }.get(days, "")

# 日数に応じた説明ラベルを返す関数
def get_days_label(days):
    return {
        1: "一昨日",
        7: "7日間",
        30: "30日間"
    }.get(days, f"{days}日間")

# date_labels.json を読み込んでキーを整数に変換
with open("date_labels.json", "r", encoding="utf-8") as f:
    raw_labels = json.load(f)
    date_labels = {int(k): v for k, v in raw_labels.items()}

# HTMLテンプレート（色分けと更新時刻・日付表示を含む）
template = Template("""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Wikipedia閲覧数ランキング</title>
    <style>
        body { font-family: sans-serif; padding: 2em; }
        h1 { margin-top: 2em; }
        h2 { margin-top: 1.5em; }
        table { border-collapse: collapse; width: 100%; margin-bottom: 1em; }
        th, td { border: 1px solid #ccc; padding: 8px; }
        th { background-color: #f2f2f2; }

        .day-1 { background-color: #e6f4e6; }
        .day-7 { background-color: #e6f0fa; }
        .day-30 { background-color: #fae6e6; }
    </style>
</head>
<body>
    <p>最終更新: {{ last_updated }}</p>

    <h1>グループA</h1>
    {% for days in [1, 7, 30] %}
        <h2>日本語版 {{ days_labels[days] }}（{{ date_labels[days] }}）</h2>
        {{ tables['groupA'][days]['ja'] | safe }}

        <h2>英語版 {{ days_labels[days] }}（{{ date_labels[days] }}）</h2>
        {{ tables['groupA'][days]['en'] | safe }}
    {% endfor %}

    <h1>グループB</h1>
    {% for days in [1, 7, 30] %}
        <h2>日本語版 {{ days_labels[days] }}（{{ date_labels[days] }}）</h2>
        {{ tables['groupB'][days]['ja'] | safe }}

        <h2>英語版 {{ days_labels[days] }}（{{ date_labels[days] }}）</h2>
        {{ tables['groupB'][days]['en'] | safe }}
    {% endfor %}
</body>
</html>
""")

# 表データ構築
tables = {
    "groupA": {},
    "groupB": {}
}

for group in ["groupA", "groupB"]:
    for days in [1, 7, 30]:
        df = load_csv(group, days)
        day_class = get_day_class(days)

        # 列名を日本語に変更してソート
        df_ja = df[["name", "ja_views"]].rename(columns={
            "name": "グループ名",
            "ja_views": "日本語の閲覧数"
        }).sort_values(by="日本語の閲覧数", ascending=False)

        df_en = df[["name", "en_views"]].rename(columns={
            "name": "グループ名",
            "en_views": "英語の閲覧数"
        }).sort_values(by="英語の閲覧数", ascending=False)

        tables[group][days] = {
            "ja": df_ja.to_html(index=False, classes=[day_class]),
            "en": df_en.to_html(index=False, classes=[day_class])
        }

# 日数ラベルを構築
days_labels = {days: get_days_label(days) for days in [1, 7, 30]}

# 更新日時を取得
JST = timezone(timedelta(hours=9))
last_updated = datetime.now(JST).strftime("%Y年%m月%d日 %H:%M:%S")

# HTML生成
html = template.render(
    tables=tables,
    last_updated=last_updated,
    date_labels=date_labels,
    days_labels=days_labels
)

# index.htmlとして保存
with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)
