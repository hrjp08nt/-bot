import discord
from discord.ext import commands
import os
import re
import random
from datetime import date
from supabase import create_client

# =====================
# 環境変数
# =====================
TOKEN = os.getenv("TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

RECOVERY_CHANNEL_ID = 1511925134129107045

# =====================
# Supabase
# =====================
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# =====================
# Discord
# =====================
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# =====================
# 冷笑ワード（そのまま）
# =====================
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

# =====================
# Supabase関数
# =====================

def load_ice():
    res = supabase.table("ice_state").select("*").eq("id", 1).execute()
    return res.data[0]

def save_ice(days, last_update):
    supabase.table("ice_state").update({
        "ice_ban_days": days,
        "last_update": last_update
    }).eq("id", 1).execute()

def add_score(user_id, name, points):
    res = supabase.table("scores").select("*").eq("user_id", user_id).execute()

    if res.data:
        user = res.data[0]
        supabase.table("scores").update({
            "score": user["score"] + points,
            "name": name
        }).eq("user_id", user_id).execute()
    else:
        supabase.table("scores").insert({
            "user_id": user_id,
            "name": name,
            "score": points
        }).execute()

# =====================
# 起動処理（そのままロジック維持）
# =====================
@bot.event
async def on_ready():

    ice = load_ice()

    today = date.today()
    last_update = date.fromisoformat(ice["last_update"])
    days_passed = (today - last_update).days

    if days_passed > 0:

        before = ice["ice_ban_days"]

        ice["ice_ban_days"] = max(0, ice["ice_ban_days"] - days_passed)

        save_ice(ice["ice_ban_days"], str(today))

        recovered = before - ice["ice_ban_days"]

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
                    f"現在のアイス禁止期間: {ice['ice_ban_days']}日"
                )

    print(f"ログイン完了: {bot.user}")

# =====================
# 冷笑検知（完全そのまま演出）
# =====================
@bot.event
async def on_message(message):

    if message.author.bot:
        return

    text = message.content.lower()

    for word, points in COLD_LAUGH_WORDS.items():

        pattern = rf"{re.escape(word)}(?:[wｗWＷ]+)"

        if re.search(pattern, text):

            user_id = str(message.author.id)

            add_score(user_id, message.author.display_name, points)

            ice = load_ice()
            ice["ice_ban_days"] += points
            save_ice(ice["ice_ban_days"], ice["last_update"])

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
                f"{ice['ice_ban_days']} 日アイスを食べられません。"
            )

            total = ice["ice_ban_days"]

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

# =====================
# コマンド（そのまま）
# =====================

@bot.command()
async def 冷笑ランキング(ctx):

    res = supabase.table("scores").select("*").order("score", desc=True).limit(10).execute()

    if not res.data:
        await ctx.send("まだ冷笑は観測されていません。")
        return

    text = "🏆 冷笑ランキング\n\n"

    medals = ["🥇", "🥈", "🥉"]

    for i, user in enumerate(res.data):
        medal = medals[i] if i < 3 else f"{i+1}."
        text += f"{medal} {user['name']} - {user['score']}pt\n"

    await ctx.send(text)


@bot.command()
async def 冷笑度(ctx, member: discord.Member = None):

    if member is None:
        member = ctx.author

    res = supabase.table("scores").select("*").eq("user_id", str(member.id)).execute()

    score = res.data[0]["score"] if res.data else 0

    await ctx.send(
        f"💀 {member.display_name} の累計冷笑ポイント: {score}pt"
    )


@bot.command()
async def かどアイス(ctx):

    ice = load_ice()

    await ctx.send(
        f"🍨 かどくんアイス被害状況\n\n"
        f"累計アイス禁止期間: {ice['ice_ban_days']}日\n"
        f"原因: サーバー内の冷笑行為"
    )


@bot.command()
@commands.has_permissions(administrator=True)
async def 復活(ctx):

    save_ice(0, str(date.today()))
    await ctx.send("✨ かどくんのアイスが復活しました！")


@bot.command()
@commands.has_permissions(administrator=True)
async def 蘇生(ctx, days: int = 1):

    ice = load_ice()

    if days <= 0:
        await ctx.send("🍨 1日以上指定してください。")
        return

    actual = min(days, ice["ice_ban_days"])

    ice["ice_ban_days"] -= actual

    save_ice(ice["ice_ban_days"], ice["last_update"])

    ices = [
        "ガリガリ君","アイスの実","スーパーカップ",
        "パピコ","ピノ","爽","MOW","雪見だいふく","あずきバー"
    ]

    await ctx.send(
        f"🍨 かどくんの{random.choice(ices)}が支給されました！\n"
        f"🍨 アイス禁止期間 -{actual}日\n"
        f"現在のアイス禁止期間: {ice['ice_ban_days']}日"
    )

# =====================
# 起動
# =====================
bot.run(TOKEN)
