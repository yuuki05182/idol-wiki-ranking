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
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Wikipedia閲覧数ランキング</title>
        <style>
            body {
                font-family: sans-serif;
                padding: 2em;
                margin: 0;
            }

            h1 { margin-top: 2em; }
            h2 { margin-top: 1.5em; }

            .table-wrapper {
                overflow-x: auto;
                margin-bottom: 1em;
            }

            table {
                border-collapse: collapse;
                width: 100%;
                min-width: 300px; /* ← 少し狭くして横スクロールを防ぐ */
                table-layout: fixed; /* ← 列幅を均等にする */
            }

            th, td {
                border: 1px solid #ccc;
                padding: 8px;
                text-align: center; /* ← 追加：中央揃え */        
            }

            th {
                background-color: #f2f2f2;
            }

            .day-1 { background-color: #e6f4e6; }
            .day-7 { background-color: #e6f0fa; }
            .day-30 { background-color: #fae6e6; }

            @media screen and (max-width: 600px) {
                body {
                    padding: 0.5em;
                }
                table {
                    font-size: 0.9em;
                }
            }
        </style>
    </head>

    <body>
<p>最終更新: {{ last_updated }}</p>

<h1>グループA</h1>
{% for days in [1, 7, 30] %}
    <h2>日本語版</h2>
    <p style="font-size:1em; margin-top:-1em; margin-bottom:1em; color:#444;">
        {{ date_labels[days]['start'] }}9時00分から{{ date_labels[days]['end'] }}8時59分
        </p>
    <div class="table-wrapper">
        {{ tables['groupA'][days]['ja'] | safe }}
    </div>

    <h2>英語版</h2>
    <p style="font-size:1em; margin-top:-1em; margin-bottom:1em; color:#444;">
   {{ date_labels[days]['start'] }}9時00分から{{ date_labels[days]['end'] }}8時59分
        </p>
    <div class="table-wrapper">
        {{ tables['groupA'][days]['en'] | safe }}
    </div>
{% endfor %}

<h1>グループB</h1>
{% for days in [1, 7, 30] %}
    <h2>日本語版</h2>
    <p style="font-size:1em; margin-top:-1em; margin-bottom:1em; color:#444;">
    {{ date_labels[days]['start'] }}9時00分から{{ date_labels[days]['end'] }}8時59分
        </p>
    <div class="table-wrapper">
        {{ tables['groupB'][days]['ja'] | safe }}
    </div>

    <h2>英語版</h2>
    <p style="font-size:1em; margin-top:-1em; margin-bottom:1em; color:#444;">
    {{ date_labels[days]['start'] }}9時00分から{{ date_labels[days]['end'] }}8時59分
        </p>
    <div class="table-wrapper">
        {{ tables['groupB'][days]['en'] | safe }}
    </div>
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

        # 閲覧数をカンマ付き文字列に変換
        df["ja_views_fmt"] = df["ja_views"].apply(lambda x: f"{int(x):,}")
        df["en_views_fmt"] = df["en_views"].apply(lambda x: f"{int(x):,}")

        # 表構築（ソートは元の数値で）
        df_ja = df[["name", "ja_views_fmt"]].rename(columns={
            "name": "グループ名",
            "ja_views_fmt": "日本語の閲覧数"
        }).sort_values(by="日本語の閲覧数", ascending=False, key=lambda x: x.str.replace(",", "").astype(int))

        df_en = df[["name", "en_views_fmt"]].rename(columns={
            "name": "グループ名",
            "en_views_fmt": "英語の閲覧数"
        }).sort_values(by="英語の閲覧数", ascending=False, key=lambda x: x.str.replace(",", "").astype(int))

        # 順位列を追加
        df_ja.insert(0, "順位", range(1, len(df_ja) + 1))
        df_en.insert(0, "順位", range(1, len(df_en) + 1))

        # HTML生成
        html_ja = df_ja.to_html(index=False, classes=[day_class])
        html_en = df_en.to_html(index=False, classes=[day_class])

        # colgroupを安全に挿入（CSSクラスを壊さない）
        html_ja = html_ja.replace(
            f'<table border="1" class="dataframe {day_class}">',
            f'<table border="1" class="dataframe {day_class}"><colgroup><col style="width:10%"><col style="width:55%"><col style="width:35%"></colgroup>',
            1
        )
        html_en = html_en.replace(
            f'<table border="1" class="dataframe {day_class}">',
            f'<table border="1" class="dataframe {day_class}"><colgroup><col style="width:10%"><col style="width:55%"><col style="width:35%"></colgroup>',
            1
        )

        # 表データを格納
        tables[group][days] = {
            "ja": html_ja,
            "en": html_en
        }

    # 日数ラベルを構築
days_labels = {days: get_days_label(days) for days in [1, 7, 30]}

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
