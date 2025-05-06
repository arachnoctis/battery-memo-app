import streamlit as st
import datetime
import json
import os
import matplotlib
matplotlib.rcParams['font.family'] = 'Meiryo'  # WindowsならMeiryoが安定
import matplotlib.pyplot as plt
import pandas as pd

st.set_page_config(page_title="バッテリーメモ", layout="centered")

st.title("🔋 今日のバッテリーを記録しよう")

# ユーザー識別（本名は禁止、ID的な長さを求める）
st.subheader("🆔 ユーザー識別")
username = st.text_input("ニックネーム（本名NG・8文字以上推奨）", max_chars=30)

if not username or len(username.strip()) < 8:
    st.warning("ニックネームは8文字以上で、本名を使わないでください。")
    st.stop()

# 個別ファイルの準備
DATA_DIR = "user_data"
os.makedirs(DATA_DIR, exist_ok=True)
DATA_FILE = os.path.join(DATA_DIR, f"{username}_battery_log.json")



# ファイルの準備（初回のみ空の辞書を保存）
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=2)

# ファイル読込（常に実行）
with open(DATA_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)
    
# 日付取得
today = str(datetime.date.today())

# スライダーとメモ入力
battery = st.slider("今日の体力（0〜100）", 0, 100, 50)
note = st.text_area("メモ（自由記入）", "")

# ✅ 正しい保存方法
if st.button("保存"):
    data[today] = {"battery": battery, "note": note}
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    st.success("✅ 記録しました。おつかれさま！")

# 最新の記録表示
# ✅ UTF-8で明示的に読み込み
with open(DATA_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)


if today in data:
    st.subheader("📅 今日の記録")
    st.write(f"体力: {data[today]['battery']} / 100")
    st.write(f"メモ: {data[today]['note']}")

# 🆕 記録の履歴一覧（新機能）
st.header("📖 記録の履歴")


# データから日付と体力を抽出（古い順に並べる）
dates = sorted(data.keys())
batteries = [data[date]["battery"] for date in dates]


# グラフ描画（Streamlit内）
st.header("📈 体力の推移グラフ")

if len(data) >= 2:
    dates = sorted(data.keys())
    batteries = [data[d]["battery"] for d in dates]

    fig, ax = plt.subplots()
    min_val = min(batteries)
    max_val = max(batteries)

# 折れ線だけを先に描画（線は緑）
    ax.plot(dates, batteries, color='green', linestyle='-')

# 各点を条件で色分け
    for i, (d, b) in enumerate(zip(dates, batteries)):
        if b == min_val:
            ax.plot(d, b, 'ro', label='最低値' if i == 0 else "")  # 赤い点
        elif b == max_val:
            ax.plot(d, b, 'bo', label='最高値' if i == 0 else "")  # 青い点
        else:
            ax.plot(d, b, 'go')  # 通常点（緑）

    ax.legend()
    ax.set_title("体力の変動")
    ax.set_xlabel("日付")
    ax.set_ylabel("体力（0〜100）")
    ax.set_ylim(0, 100)
    ax.grid(True)

    # X軸のラベル回転（これだけで十分）
    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')

    with st.expander("📊 グラフを見る"):
        st.pyplot(fig)

else:
    st.info("グラフを表示するには2件以上の記録が必要です。")
# 🛠 任意日の編集
st.header("🛠 任意日の編集")

if data:
    selected_date = st.selectbox("編集したい日付を選択", sorted(data.keys(), reverse=True))

    selected_battery = data[selected_date]["battery"]
    selected_note = data[selected_date]["note"]

    new_battery = st.slider("体力（0〜100）", 0, 100, selected_battery, key="edit_battery")
    new_note = st.text_area("メモ", value=selected_note, key="edit_note")

    if st.button("この日の記録を更新"):
        data[selected_date] = {"battery": new_battery, "note": new_note}
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        st.success(f"{selected_date} の記録を更新しました。")
else:
    st.info("記録が存在しません。")
    
# 🧹 記録の削除
st.header("🧹 記録の削除")

if data:
    delete_date = st.selectbox("削除したい日付を選択", sorted(data.keys(), reverse=True), key="delete_select")

    if st.button("この日の記録を削除", key="delete_button"):
        if delete_date in data:
            del data[delete_date]
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            st.success(f"{delete_date} の記録を削除しました。")
else:
    st.info("削除できる記録が存在しません。")
# データをDataFrame化（空チェックを追加）
if not data:
    st.info("記録がまだ存在しません。記録を追加するとグラフと統計が表示されます。")
else:
    df = pd.DataFrame([
        {"date": d, "battery": data[d]["battery"]}
        for d in data
    ])
    df["date"] = pd.to_datetime(df["date"])
    df["week"] = df["date"].dt.to_period("W").astype(str)
    df["month"] = df["date"].dt.strftime("%Y年%m月")

    # グループごとに平均
    weekly_avg = df.groupby("week")["battery"].mean().reset_index()
    monthly_avg = df.groupby("month")["battery"].mean().reset_index()

    # 表示
    st.subheader("📅 週ごとの平均体力")
    st.dataframe(weekly_avg)
    st.bar_chart(weekly_avg.set_index("week"))

    st.subheader("🗓 月ごとの平均体力")
    st.dataframe(monthly_avg)
    st.bar_chart(monthly_avg.set_index("month"))



if data:
    # 日付で降順に表示
    for date_key in sorted(data.keys(), reverse=True):
        if date_key == today:
            continue
        st.markdown(f"### 📅 {date_key}")
        st.write(f"🔋 体力: {data[date_key]['battery']}")
        st.write(f"📝 メモ: {data[date_key]['note']}")
        st.markdown("---")
else:
    st.info("記録がまだ存在しません。")
