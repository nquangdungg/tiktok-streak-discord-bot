"""
TikTok Streak Discord Bot
=========================
Quản lý cookies, contacts và chạy streak bot qua Discord.
"""

import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
import os
import asyncio
import logging
from datetime import datetime

from config import (
    DISCORD_TOKEN,
    PREFIX,
    COOKIES_FILE,
    CONTACTS_FILE,
    DATA_DIR,
    STREAK_MESSAGE,
)
from streak_bot import TikTokStreakBot

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("discord_bot")

intents = discord.Intents.default()
intents.message_content = True
intents.dm_messages = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# Tránh chạy song song
is_running = False


def load_contacts():
    if not os.path.exists(CONTACTS_FILE):
        return []
    try:
        with open(CONTACTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("contacts", [])
    except Exception:
        return []


def save_contacts(contacts):
    with open(CONTACTS_FILE, "w", encoding="utf-8") as f:
        json.dump({"contacts": contacts}, f, indent=2, ensure_ascii=False)


def has_cookies():
    return os.path.exists(COOKIES_FILE) and os.path.getsize(COOKIES_FILE) > 10


@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
    try:
        synced = await bot.tree.sync()
        logger.info(f"Synced {len(synced)} slash commands")
    except Exception as e:
        logger.error(f"Sync error: {e}")
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.watching, name="TikTok Streaks 🔥")
    )


# ==================== SLASH COMMANDS ====================

@bot.tree.command(name="status", description="Xem trạng thái bot (cookies, contacts...)")
async def status_cmd(interaction: discord.Interaction):
    contacts = load_contacts()
    cookies_ok = has_cookies()
    embed = discord.Embed(
        title="📊 Trạng thái TikTok Streak Bot",
        color=0x00FF88 if cookies_ok else 0xFF5555,
        timestamp=datetime.utcnow(),
    )
    embed.add_field(name="🍪 Cookies", value="✅ Đã có" if cookies_ok else "❌ Chưa có / hết hạn", inline=True)
    embed.add_field(name="👥 Contacts", value=f"**{len(contacts)}** người", inline=True)
    embed.add_field(name="💬 Message mặc định", value=f"`{STREAK_MESSAGE}`", inline=False)
    if contacts:
        preview = ", ".join([f"`{c}`" for c in contacts[:10]])
        if len(contacts) > 10:
            preview += f" ... (+{len(contacts)-10})"
        embed.add_field(name="Danh sách", value=preview, inline=False)
    embed.set_footer(text="Dùng /help để xem hướng dẫn")
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="help", description="Hướng dẫn sử dụng bot")
async def help_cmd(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🔥 TikTok Streak Discord Bot - Hướng dẫn",
        description=(
            "Bot tự động gửi tin giữ streak TikTok.\n"
            "**Lưu ý:** Automation có thể vi phạm ToS TikTok → rủi ro khóa acc."
        ),
        color=0x5865F2,
    )
    embed.add_field(
        name="1️⃣ Cài cookies (quan trọng)",
        value=(
            "1. Login TikTok trên trình duyệt\n"
            "2. Dùng extension (EditThisCookie / Cookie-Editor) export cookies dạng JSON\n"
            "3. Gửi file `cookies.json` vào **DM** với bot\n"
            "   hoặc dùng lệnh `/set_cookies` rồi paste JSON"
        ),
        inline=False,
    )
    embed.add_field(
        name="2️⃣ Quản lý contacts",
        value=(
            "`/add_contact username` – thêm người\n"
            "`/remove_contact username` – xóa\n"
            "`/list_contacts` – xem danh sách\n"
            "`/clear_contacts` – xóa hết"
        ),
        inline=False,
    )
    embed.add_field(
        name="3️⃣ Chạy bot",
        value=(
            "`/run_streak` – gửi tin với message mặc định\n"
            "`/run_streak message:Nội dung tùy chỉnh` – gửi message riêng\n"
            "`/test_streak` – chỉ tìm contacts, không gửi thật"
        ),
        inline=False,
    )
    embed.add_field(
        name="4️⃣ Khác",
        value="`/status` – xem trạng thái\n`/set_message Nội dung` – đổi message mặc định",
        inline=False,
    )
    embed.set_footer(text="Cookies nên gửi qua DM để bảo mật")
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="add_contact", description="Thêm username TikTok vào danh sách")
@app_commands.describe(username="Username TikTok (không cần @)")
async def add_contact(interaction: discord.Interaction, username: str):
    username = username.strip().lstrip("@")
    if not username:
        await interaction.response.send_message("❌ Username không hợp lệ", ephemeral=True)
        return
    contacts = load_contacts()
    if username.lower() in [c.lower() for c in contacts]:
        await interaction.response.send_message(f"⚠️ `{username}` đã có trong danh sách", ephemeral=True)
        return
    contacts.append(username)
    save_contacts(contacts)
    await interaction.response.send_message(
        f"✅ Đã thêm `{username}`\nTổng: **{len(contacts)}** contacts", ephemeral=True
    )


@bot.tree.command(name="remove_contact", description="Xóa username khỏi danh sách")
@app_commands.describe(username="Username cần xóa")
async def remove_contact(interaction: discord.Interaction, username: str):
    username = username.strip().lstrip("@")
    contacts = load_contacts()
    new_list = [c for c in contacts if c.lower() != username.lower()]
    if len(new_list) == len(contacts):
        await interaction.response.send_message(f"❌ Không tìm thấy `{username}`", ephemeral=True)
        return
    save_contacts(new_list)
    await interaction.response.send_message(
        f"✅ Đã xóa `{username}`\nCòn lại: **{len(new_list)}** contacts", ephemeral=True
    )


@bot.tree.command(name="list_contacts", description="Xem danh sách contacts")
async def list_contacts(interaction: discord.Interaction):
    contacts = load_contacts()
    if not contacts:
        await interaction.response.send_message("📭 Danh sách trống", ephemeral=True)
        return
    text = "\n".join([f"{i+1}. `{c}`" for i, c in enumerate(contacts)])
    embed = discord.Embed(title=f"👥 Contacts ({len(contacts)})", description=text, color=0x00BFFF)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="clear_contacts", description="Xóa toàn bộ danh sách contacts")
async def clear_contacts(interaction: discord.Interaction):
    save_contacts([])
    await interaction.response.send_message("🗑️ Đã xóa toàn bộ contacts", ephemeral=True)


@bot.tree.command(name="set_message", description="Đổi message mặc định khi gửi streak")
@app_commands.describe(message="Nội dung tin nhắn")
async def set_message(interaction: discord.Interaction, message: str):
    # Lưu tạm vào file đơn giản
    msg_file = os.path.join(DATA_DIR, "custom_message.txt")
    with open(msg_file, "w", encoding="utf-8") as f:
        f.write(message)
    await interaction.response.send_message(f"✅ Message mặc định đã đổi thành:\n`{message}`", ephemeral=True)


def get_default_message():
    msg_file = os.path.join(DATA_DIR, "custom_message.txt")
    if os.path.exists(msg_file):
        with open(msg_file, "r", encoding="utf-8") as f:
            return f.read().strip() or STREAK_MESSAGE
    return STREAK_MESSAGE


@bot.tree.command(name="set_cookies", description="Cập nhật cookies TikTok (paste JSON)")
@app_commands.describe(cookies_json="Nội dung JSON cookies (hoặc gửi file qua DM)")
async def set_cookies(interaction: discord.Interaction, cookies_json: str):
    try:
        data = json.loads(cookies_json)
        if not isinstance(data, list):
            raise ValueError("Cookies phải là mảng JSON")
        with open(COOKIES_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        await interaction.response.send_message(
            f"✅ Đã lưu **{len(data)}** cookies thành công!", ephemeral=True
        )
    except Exception as e:
        await interaction.response.send_message(
            f"❌ Lỗi parse JSON: `{e}`\nHãy chắc chắn là mảng cookies hợp lệ.", ephemeral=True
        )


@bot.event
async def on_message(message: discord.Message):
    # Nhận file cookies qua DM
    if message.author.bot:
        return
    if isinstance(message.channel, discord.DMChannel) and message.attachments:
        for att in message.attachments:
            if att.filename.endswith(".json") or "cookie" in att.filename.lower():
                try:
                    content = await att.read()
                    data = json.loads(content.decode("utf-8"))
                    if isinstance(data, list):
                        with open(COOKIES_FILE, "w", encoding="utf-8") as f:
                            json.dump(data, f, indent=2)
                        await message.channel.send(
                            f"✅ Đã nhận và lưu **{len(data)}** cookies từ file `{att.filename}`!"
                        )
                    else:
                        await message.channel.send("❌ File JSON không phải mảng cookies.")
                except Exception as e:
                    await message.channel.send(f"❌ Lỗi đọc file: `{e}`")
                return
    await bot.process_commands(message)


async def run_streak_task(interaction: discord.Interaction, custom_message: str = None, test_mode: bool = False):
    global is_running
    if is_running:
        await interaction.followup.send("⚠️ Bot đang chạy rồi, đợi xong đã nhé!", ephemeral=True)
        return

    if not has_cookies():
        await interaction.followup.send(
            "❌ Chưa có cookies. Hãy dùng `/set_cookies` hoặc gửi file cookies.json vào DM bot.",
            ephemeral=True,
        )
        return

    contacts = load_contacts()
    if not contacts:
        await interaction.followup.send("❌ Danh sách contacts trống. Dùng `/add_contact` trước.", ephemeral=True)
        return

    is_running = True
    channel = interaction.channel

    async def progress(msg: str):
        try:
            await channel.send(msg)
        except Exception:
            pass

    try:
        bot_instance = TikTokStreakBot(
            headless=True,
            test_mode=test_mode,
            custom_message=custom_message or get_default_message(),
            progress_callback=progress,
        )
        # Chạy trong thread pool vì DrissionPage blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, lambda: asyncio.run(bot_instance.run()))
        # Vì run() là async, cần cách khác
    except Exception as e:
        await channel.send(f"❌ Lỗi khi chạy: `{e}`")
    finally:
        is_running = False


# Fix: vì run() là async nhưng DrissionPage blocking, ta viết lại wrapper
async def execute_streak(interaction: discord.Interaction, custom_message: str = None, test_mode: bool = False):
    global is_running
    if is_running:
        await interaction.followup.send("⚠️ Bot đang chạy, vui lòng đợi!", ephemeral=True)
        return

    if not has_cookies():
        await interaction.followup.send(
            "❌ Chưa có cookies hợp lệ.\nGửi file `cookies.json` vào **DM** bot hoặc dùng `/set_cookies`.",
            ephemeral=True,
        )
        return

    contacts = load_contacts()
    if not contacts:
        await interaction.followup.send("❌ Chưa có contact nào. Dùng `/add_contact username`", ephemeral=True)
        return

    is_running = True
    channel = interaction.channel

    async def progress(msg: str):
        try:
            # chia nhỏ nếu quá dài
            if len(msg) > 1900:
                for i in range(0, len(msg), 1900):
                    await channel.send(msg[i:i+1900])
            else:
                await channel.send(msg)
        except Exception:
            pass

    try:
        streak_bot = TikTokStreakBot(
            headless=True,
            test_mode=test_mode,
            custom_message=custom_message or get_default_message(),
            progress_callback=progress,
        )
        result = await streak_bot.run()
    except Exception as e:
        logger.exception("Execute streak failed")
        await channel.send(f"❌ Lỗi nghiêm trọng: `{e}`")
    finally:
        is_running = False


@bot.tree.command(name="run_streak", description="Chạy bot gửi tin giữ streak ngay")
@app_commands.describe(message="Tin nhắn tùy chỉnh (để trống = dùng mặc định)")
async def run_streak(interaction: discord.Interaction, message: str = None):
    await interaction.response.defer(thinking=True)
    await interaction.followup.send("🚀 Đã nhận lệnh, bắt đầu chạy bot...")
    await execute_streak(interaction, custom_message=message, test_mode=False)


@bot.tree.command(name="test_streak", description="Chạy thử (chỉ tìm contacts, không gửi tin thật)")
async def test_streak(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)
    await interaction.followup.send("🧪 Chế độ TEST – sẽ không gửi tin thật...")
    await execute_streak(interaction, test_mode=True)


# ==================== PREFIX COMMANDS (backup) ====================

@bot.command(name="status")
async def status_prefix(ctx):
    contacts = load_contacts()
    cookies_ok = has_cookies()
    await ctx.send(
        f"**Status**\n"
        f"Cookies: {'✅' if cookies_ok else '❌'}\n"
        f"Contacts: {len(contacts)}\n"
        f"Message: `{get_default_message()}`"
    )


if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("❌ Thiếu DISCORD_TOKEN trong .env")
        exit(1)
    bot.run(DISCORD_TOKEN)
