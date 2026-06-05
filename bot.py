import discord
from discord.ext import commands
import json
import os
import re
import random
from datetime import date


TOKEN = os.getenv("TOKEN")
RECOVERY_CHANNEL_ID = 1511925134129107045

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

DATA_FILE = "coldlaugh_data.json"

# 冷笑ワードとポイント
COLD_LAUGH_WORDS = {
    "うお": 1,
    "かっけー": 1,
    "どひゃー": 2,
    "どわー": 2,
    "ういー": 5,
    "ほーん": 3,
    "あ、はーい": 3,
    "はいはい": 5,
    "なるほどねぇ": 3,
    "おもろ": 2,
}


# データ読み込み
def load_data():
    if not os.path.exists(DATA_FILE):
        return {
    "scores": {},
    "ice_ban_days": 0,
    "last_update": str(date.today())
}

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# データ保存
def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

data = load_data()

# Ensure required keys exist
if "scores" not in data:
    data["scores"] = {}
if "ice_ban_days" not in data:
    data["ice_ban_days"] = 0
if "last_update" not in data:
    data["last_update"] = str(date.today())

@bot.event
async def on_ready():

    today = date.today()

    last_update = date.fromisoformat(
        data.get("last_update", str(today))
    )

    days_passed = (today - last_update).days

    if days_passed > 0:

        before = data["ice_ban_days"]

        data["ice_ban_days"] = max(
            0,
            data["ice_ban_days"] - days_passed
        )

        data["last_update"] = str(today)

        save_data(data)

        recovered = before - data["ice_ban_days"]

        if recovered > 0:

            recovery_messages = [
                "冷凍庫から未開封のアイスが発見されました",
                "アイス支援物資が到着しました",
                "冷笑時効制度によりアイスが返還されました",
                "冷笑裁判所がアイス返還命令を出しました",
                "冷笑被害者救済基金からアイスが支給されました",
                "温かい発言が観測されたためアイスが補填されました",
                "善行ポイントが貯まったためアイスが返ってきました",
                "サーバー全体の良心によりアイスが復活しました",
                "謎のアイス寄付者が現れました",
                "冷笑税の還付によりアイスが返ってきました"
            ]

            channel = bot.get_channel(RECOVERY_CHANNEL_ID)

            if channel:
                await channel.send(
                    f"🍨 かどくんの{random.choice(recovery_messages)}！\n\n"
                    f"🍨 アイス禁止期間 -{recovered}日\n"
                    f"現在のアイス禁止期間: "
                    f"{data['ice_ban_days']}日"
                )

    print(f"ログイン完了: {bot.user}")
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    text = message.content.lower()

    for word, points in COLD_LAUGH_WORDS.items():

        pattern = rf"{re.escape(word)}(?:[wｗWＷ]+)"

        if re.search(pattern, text):

            user_id = str(message.author.id)

            if user_id not in data["scores"]:
                data["scores"][user_id] = {
                    "name": message.author.display_name,
                    "score": 0
                }

            data["scores"][user_id]["name"] = message.author.display_name
            data["scores"][user_id]["score"] += points

            data["ice_ban_days"] += points

            save_data(data)

            stars = min(points, 5)
            cold_level = "★" * stars + "☆" * (5 - stars)

            msg = (
                f"⚠️ 冷笑を検出しました！😅\n\n"
                f"投稿者: {message.author.mention}\n"
                f"元メッセージ:\n"
                f"> {message.content}\n\n"
                f"冷笑度: {cold_level}\n"
                f"💀 冷笑ポイント +{points}\n"
                f"🍨 かどくんのアイス禁止期間 +{points}日\n\n"
                f"現在、かどくんは累計 "
                f"{data['ice_ban_days']} 日アイスを食べられません。"
            )

            # 特殊イベント
            total = data["ice_ban_days"]

            if total >= 1000:
                msg += "\n\n🌍 冷笑災害認定"
            elif total >= 365:
                msg += "\n\n☠️ かどくんは1年間アイスを失いました"
            elif total >= 100:
                msg += "\n\n🚨 冷笑被害が深刻化しています"
            elif total >= 30:
                msg += "\n\n📢 かどくんは1か月アイスを失いました"

            await message.channel.send(msg)

            break

    await bot.process_commands(message)

# ランキング
@bot.command()
async def 冷笑ランキング(ctx):

    ranking = sorted(
        data["scores"].values(),
        key=lambda x: x["score"],
        reverse=True
    )

    if not ranking:
        await ctx.send("まだ冷笑は観測されていません。")
        return

    text = "🏆 冷笑ランキング\n\n"

    medals = ["🥇", "🥈", "🥉"]

    for i, user in enumerate(ranking[:10]):
        medal = medals[i] if i < 3 else f"{i+1}."
        text += f"{medal} {user['name']} - {user['score']}pt\n"

    await ctx.send(text)

# 個人ポイント
@bot.command()
async def 冷笑度(ctx, member: discord.Member = None):

    if member is None:
        member = ctx.author

    uid = str(member.id)

    score = data["scores"].get(
        uid,
        {"score": 0}
    )["score"]

    await ctx.send(
        f"💀 {member.display_name} の累計冷笑ポイント: {score}pt"
    )

# アイス状況
@bot.command()
async def かどアイス(ctx):

    await ctx.send(
        f"🍨 かどくんアイス被害状況\n\n"
        f"累計アイス禁止期間: {data['ice_ban_days']}日\n"
        f"原因: サーバー内の冷笑行為"
    )

# 管理者用リセット
@bot.command()
@commands.has_permissions(administrator=True)
async def 復活(ctx):

    data["ice_ban_days"] = 0
    save_data(data)

    await ctx.send(
        "✨ かどくんのアイスが復活しました！"
    )

#管理者用蘇生
@bot.command()
@commands.has_permissions(administrator=True)
async def 蘇生(ctx, days: int = 1):

    if days <= 0:
        await ctx.send("🍨 1日以上指定してください。")
        return

    if data["ice_ban_days"] <= 0:
        await ctx.send(
            "🍨 かどくんはすでに自由にアイスを食べられます。"
        )
        return

    actual = min(days, data["ice_ban_days"])

    data["ice_ban_days"] -= actual
    save_data(data)

    ices = [
        "ガリガリ君",
        "アイスの実",
        "スーパーカップ",
        "パピコ",
        "ピノ",
        "爽",
        "MOW",
        "雪見だいふく",
        "あずきバー"
    ]

    await ctx.send(
        f"🍨 かどくんの{random.choice(ices)}が支給されました！\n"
        f"🍨 アイス禁止期間 -{actual}日\n"
        f"現在のアイス禁止期間: {data['ice_ban_days']}日"
    )