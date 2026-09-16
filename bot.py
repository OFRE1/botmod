import datetime
import discord
import os
from discord import app_commands
from discord.ext import commands # hidden prefix

DEV_ID = 1420049811687604357 # Only justafrog_367 can use this 



# --- BƯỚC 1: KHỞI TẠO INTENTS & BOT (PHẢI NẰM TRÊN CÙNG) ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="sudo ", intents=intents)


# Hàm kiểm tra xem người gõ lệnh có phải là Dev không
def is_dev():
    async def predicate(ctx: commands.Context):
        return ctx.author.id == DEV_ID
    return commands.check(predicate)

@bot.command(name="ban")
@is_dev()
async def sudo_ban(ctx, member: discord.Member = None, *, reason: str = "Không có lý do"):
    if not member:
        await ctx.send("❌ Thiếu tham số! Cú pháp: `sudo ban @user [lý do]`", delete_after=5)
        return
        
    if member.top_role >= ctx.author.top_role:
        await ctx.send("❌ Bạn không thể ban người có vai trò bằng hoặc cao hơn bạn!", delete_after=5)
        return

    try:
        await member.send(f"⚠️ Bạn đã bị ban khỏi **{ctx.guild.name}** qua lệnh sudo.\nLý do: `{reason}`")
    except discord.Forbidden:
        pass

    try:
        await ctx.guild.ban(member, reason=reason)
        await writelogs(ctx.guild, mode="ban", user=member, moderator=ctx.author, reason=reason)
        await ctx.send(f"✅ Đã ban thành công **{member.name}**.", delete_after=5)
    except Exception as e:
        await ctx.send(f"❌ Lỗi: {e}", delete_after=5)


# --- BẢN SAO PREFIX: SUDO KICK ---
@bot.command(name="kick")
@is_dev()
async def sudo_kick(ctx, member: discord.Member = None, *, reason: str = "Không có lý do"):
    if not member:
        await ctx.send("❌ Thiếu tham số! Cú pháp: `sudo kick @user [lý do]`", delete_after=5)
        return

    if member.top_role >= ctx.author.top_role:
        await ctx.send("❌ Bạn không thể kick người có vai trò bằng hoặc cao hơn bạn!", delete_after=5)
        return

    try:
        await member.send(f"⚠️ Bạn đã bị kick khỏi **{ctx.guild.name}** qua lệnh sudo.\nLý do: `{reason}`")
    except discord.Forbidden:
        pass

    try:
        await ctx.guild.kick(member, reason=reason)
        await writelogs(ctx.guild, mode="kick", user=member, moderator=ctx.author, reason=reason)
        await ctx.send(f"✅ Đã kick thành công **{member.name}**.", delete_after=5)
    except Exception as e:
        await ctx.send(f"❌ Lỗi: {e}", delete_after=5)


# --- BẢN SAO PREFIX: SUDO TIMEOUT ---
@bot.command(name="timeout")
@is_dev()
async def sudo_timeout(ctx, member: discord.Member = None, minutes: int = 5, *, reason: str = "Không có lý do"):
    if not member:
        await ctx.send("❌ Thiếu tham số! Cú pháp: `sudo timeout @user [số phút] [lý do]`", delete_after=5)
        return

    if member.top_role >= ctx.author.top_role:
        await ctx.send("❌ Bạn không thể timeout người có vai trò bằng hoặc cao hơn bạn!", delete_after=5)
        return

    try:
        duration_delta = datetime.timedelta(minutes=minutes)
        await member.timeout(duration_delta, reason=reason)
        
        await writelogs(
            ctx.guild, 
            mode="timeout", 
            user=member, 
            moderator=ctx.author, 
            duration=f"{minutes} phút", 
            reason=reason
        )
        await ctx.send(f"✅ Đã timeout **{member.name}** trong {minutes} phút.", delete_after=5)
    except Exception as e:
        await ctx.send(f"❌ Lỗi: {e}", delete_after=5)


# --- BẢN SAO PREFIX: SUDO WARN (CÓ EASTER EGG) ---
@bot.command(name="warn")
@is_dev()
async def sudo_warn(ctx, member: discord.Member = None, *, reason: str = "Không có lý do"):
    if not member:
        await ctx.send("❌ Thiếu tham số! Cú pháp: `sudo warn @user [nội dung]`", delete_after=5)
        return

    # --- EASTER EGG KHI WARN BOT QUA SUDO ---
    if member.id == ctx.bot.user.id:
        await ctx.send("ê nha anh bạn làm gì ếch đấy 🐸")
        return

    try:
        try:
            await member.send(f"⚠️ Bạn nhận được cảnh báo tại **{ctx.guild.name}**.\nNội dung: `{reason}`")
        except discord.Forbidden:
            pass

        await writelogs(ctx.guild, mode="warn", user=member, moderator=ctx.author, reason=reason)
        await ctx.send(f"✅ Đã cảnh báo **{member.name}** thành công.", delete_after=5)
    except Exception as e:
        await ctx.send(f"❌ Lỗi: {e}", delete_after=5)


# --- XỬ LÝ KHI KẺ KHÁC CỐ TÌNH GÕ LỆNH SUDO ---
@sudo_ban.error
@sudo_kick.error
@sudo_timeout.error
@sudo_warn.error
async def sudo_errors(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("Chúc mừng vì đào được easter eggs : prefix sudo", delete_after=5)
# Bộ nhớ RAM lưu cấu hình kênh log theo Guild ID
log_configs = {}

# --- HÀM GHI LOG TÙY BIẾN (MODE SYSTEM) ---
async def writelogs(guild: discord.Guild, mode: str, **kwargs):
    guild_id = guild.id
    if guild_id not in log_configs:
        return
        
    channel_id = log_configs[guild_id]
    log_channel = guild.get_channel(channel_id)
    if not log_channel:
        return

    user = kwargs.get("user")
    embed = discord.Embed(timestamp=discord.utils.utcnow())
    
    if user:
        embed.set_thumbnail(url=user.display_avatar.url)

    # --- NHÓM MODERATION (Ban, Kick, Warn, Timeout) ---
    if mode in ["ban", "kick", "warn", "timeout"]:
        moderator = kwargs.get("moderator", "Không rõ")
        reason = kwargs.get("reason", "Không có lý do")
        
        if user:
            embed.add_field(name="Thành viên", value=f"{user.name} (`{user.id}`)", inline=False)
        embed.add_field(name="Người thực hiện", value=str(moderator), inline=True)

        if mode == "ban":
            embed.title = "🔨 THÀNH VIÊN BỊ BAN"
            embed.color = discord.Color.red()
            embed.add_field(name="Lý do", value=reason, inline=False)
        elif mode == "kick":
            embed.title = "👢 THÀNH VIÊN BỊ KICK"
            embed.color = discord.Color.orange()
            embed.add_field(name="Lý do", value=reason, inline=False)
        elif mode == "warn":
            embed.title = "⚠️ THÀNH VIÊN BỊ CẢNH BÁO"
            embed.color = discord.Color.yellow()
            embed.add_field(name="Nội dung", value=reason, inline=False)
        elif mode == "timeout":
            duration = kwargs.get("duration", "Không rõ")
            embed.title = "⏳ THÀNH VIÊN BỊ TIMEOUT"
            embed.color = discord.Color.purple()
            embed.add_field(name="Thời gian", value=duration, inline=True)
            embed.add_field(name="Lý do", value=reason, inline=False)

    # --- NHÓM SỰ KIỆN THÀNH VIÊN (Join, Left) ---
    elif mode == "join":
        embed.title = "📥 THÀNH VIÊN THAM GIA"
        embed.color = discord.Color.green()
        embed.add_field(name="Thành viên", value=f"{user.mention} (`{user.name}`)", inline=False)
        embed.add_field(name="Tổng số thành viên", value=str(guild.member_count), inline=True)
        
    elif mode == "left":
        embed.title = "📤 THÀNH VIÊN RỜI SERVER"
        embed.color = discord.Color.dark_grey()
        embed.add_field(name="Thành viên", value=f"{user.name} (`{user.id}`)", inline=False)
        embed.add_field(name="Tổng số thành viên", value=str(guild.member_count), inline=True)

    # --- NHÓM TIN NHẮN (Msg Edit, Msg Delete) ---
    elif mode == "msg_delete":
        msg = kwargs.get("message")
        embed.title = "🗑️ TIN NHẮN BỊ XÓA"
        embed.color = discord.Color.red()
        embed.add_field(name="Tác giả", value=f"{user.mention} (`{user.name}`)", inline=False)
        embed.add_field(name="Kênh", value=msg.channel.mention, inline=True)
        embed.add_field(name="Nội dung", value=msg.content if msg.content else "*[Tin nhắn trống / Hình ảnh/Embed]*", inline=False)
        
    elif mode == "msg_edit":
        before = kwargs.get("before")
        after = kwargs.get("after")
        embed.title = "✏️ TIN NHẮN BỊ CHỈNH SỬA"
        embed.color = discord.Color.blue()
        embed.add_field(name="Tác giả", value=f"{user.mention} (`{user.name}`)", inline=False)
        embed.add_field(name="Kênh", value=before.channel.mention, inline=True)
        embed.add_field(name="Trước khi sửa", value=before.content if before.content else "*[Trống]*", inline=False)
        embed.add_field(name="Sau khi sửa", value=after.content if after.content else "*[Trống]*", inline=False)

    await log_channel.send(embed=embed)


# ==========================================
# CÁC SỰ KIỆN TỰ ĐỘNG BẮT (EVENTS)
# ==========================================

@bot.event
async def on_member_join(member: discord.Member):
    await writelogs(member.guild, mode="join", user=member)

@bot.event
async def on_member_remove(member: discord.Member):
    await writelogs(member.guild, mode="left", user=member)

@bot.event
async def on_message_delete(message: discord.Message):
    # Bỏ qua tin nhắn từ bot hoặc không thuộc server
    if message.author.bot or not message.guild:
        return
    await writelogs(message.guild, mode="msg_delete", user=message.author, message=message)

@bot.event
async def on_message_edit(before: discord.Message, after: discord.Message):
    # Bỏ qua bot, tin nhắn không có guild hoặc nội dung không đổi (tránh trường hợp embed tự load link)
    if before.author.bot or not before.guild or before.content == after.content:
        return
    await writelogs(before.guild, mode="msg_edit", user=before.author, before=before, after=after)


# --- 1. LỆNH SLASH CONFIG KÊNH LOG ---
@bot.tree.command(name="setlog", description="Cài đặt kênh gửi nhật ký hành động của server")
@app_commands.describe(channel="Chọn kênh để làm kênh log")
@app_commands.checks.has_permissions(administrator=True)
async def setlog(interaction: discord.Interaction, channel: discord.TextChannel):
    log_configs[interaction.guild_id] = channel.id
    await interaction.response.send_message(f"✅ Đã thiết lập kênh log thành công tại {channel.mention}!", ephemeral=True)


# --- 2. LỆNH SLASH: /BAN ---
@bot.tree.command(name="ban", description="Ban thành viên khỏi server")
@app_commands.describe(member="Thành viên cần ban", reason="Lý do ban")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "Không có lý do"):
    if member.top_role >= interaction.user.top_role:
        await interaction.response.send_message("❌ Bạn không thể ban người có vai trò bằng hoặc cao hơn bạn!", ephemeral=True)
        return

    try:
        await member.send(f"⚠️ Bạn đã bị ban khỏi **{interaction.guild.name}**.\nLý do: `{reason}`")
    except discord.Forbidden:
        pass

    try:
        await interaction.guild.ban(member, reason=reason)
        await writelogs(interaction.guild, mode="ban", user=member, moderator=interaction.user, reason=reason)
        await interaction.response.send_message(f"✅ Đã ban thành công **{member.name}**.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Lỗi: {e}", ephemeral=True)


# --- 3. LỆNH SLASH: /KICK ---
@bot.tree.command(name="kick", description="Kick thành viên khỏi server")
@app_commands.describe(member="Thành viên cần kick", reason="Lý do kick")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "Không có lý do"):
    if member.top_role >= interaction.user.top_role:
        await interaction.response.send_message("❌ Bạn không thể kick người có vai trò bằng hoặc cao hơn bạn!", ephemeral=True)
        return

    try:
        await member.send(f"⚠️ Bạn đã bị kick khỏi **{interaction.guild.name}**.\nLý do: `{reason}`")
    except discord.Forbidden:
        pass

    try:
        await interaction.guild.kick(member, reason=reason)
        await writelogs(interaction.guild, mode="kick", user=member, moderator=interaction.user, reason=reason)
        await interaction.response.send_message(f"✅ Đã kick thành công **{member.name}**.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Lỗi: {e}", ephemeral=True)


# --- 4. LỆNH SLASH: /TIMEOUT (CẤM CHAT) ---
@bot.tree.command(name="timeout", description="Cấm chat (timeout) thành viên trong khoảng thời gian")
@app_commands.describe(
    member="Thành viên cần timeout",
    minutes="Số phút timeout",
    reason="Lý do timeout"
)
@app_commands.checks.has_permissions(moderate_members=True)
async def timeout(interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str = "Không có lý do"):
    if member.top_role >= interaction.user.top_role:
        await interaction.response.send_message("❌ Bạn không thể timeout người có vai trò bằng hoặc cao hơn bạn!", ephemeral=True)
        return

    try:
        duration_delta = datetime.timedelta(minutes=minutes)
        await member.timeout(duration_delta, reason=reason)
        
        await writelogs(
            interaction.guild, 
            mode="timeout", 
            user=member, 
            moderator=interaction.user, 
            duration=f"{minutes} phút", 
            reason=reason
        )
        await interaction.response.send_message(f"✅ Đã timeout **{member.name}** trong {minutes} phút.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Lỗi: {e}", ephemeral=True)


# --- 5. LỆNH SLASH: /WARN ---
@bot.tree.command(name="warn", description="Cảnh báo (warn) thành viên")
@app_commands.describe(member="Thành viên cần cảnh báo", reason="Nội dung cảnh báo")
@app_commands.checks.has_permissions(manage_messages=True)
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str = "Không có lý do"):
    
    # --- EASTER EGG: NẾU DÁM WARN BOT ---
    if member.id == interaction.client.user.id:
        await interaction.response.send_message("Ê nha anh bạn làm gì ếch đấy 🐸", ephemeral=False)
        return

    try:
        # Gửi DM cảnh báo cho user thông thường
        try:
            await member.send(f"⚠️ Bạn nhận được cảnh báo tại **{interaction.guild.name}**.\nNội dung: `{reason}`")
        except discord.Forbidden:
            pass

        await writelogs(interaction.guild, mode="warn", user=member, moderator=interaction.user, reason=reason)
        await interaction.response.send_message(f"✅ Đã cảnh báo **{member.name}** thành công.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Lỗi: {e}", ephemeral=True)


# --- XỬ LÝ LỖI THIẾU QUYỀN HẠN CHUNG ---
@setlog.error
@ban.error
@kick.error
@timeout.error
@warn.error
async def command_error_handler(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.checks.MissingPermissions):
        await interaction.response.send_message("❌ Bạn không có đủ quyền hạn để sử dụng lệnh này!", ephemeral=True)
        
# AUTOMOD
@bot.event
async def on_message(message: discord.Message):
    # 1. Bỏ qua tin nhắn của bot, tin nhắn ngoài server hoặc không có nội dung
    if message.author.bot or not message.guild or not message.content:
        return

    # Bỏ qua Admin/Mod để tránh bị bot khóa nhầm
    if message.author.guild_permissions.manage_messages:
        await bot.process_commands(message)
        return

    user_id = message.author.id
    current_time = time.time()
    content_lower = message.content.lower()

    # --- KIỂM TRA 1: TỪ KHÓA CẤM / PHISHING LINK ---
    for word in BLACKLIST_WORDS:
        if word in content_lower:
            try:
                await message.delete()
                # Tự động timeout 5 phút cảnh cáo
                import datetime
                await message.author.timeout(datetime.timedelta(minutes=5), reason="AutoMod: Gửi link/từ khóa độc hại")
            except discord.Forbidden:
                pass

            # Ghi log qua hàm writelogs
            await writelogs(
                message.guild, 
                mode="automod", 
                user=message.author, 
                violation="Chứa từ khóa/link cấm (Phishing/Scam)", 
                content=message.content
            )
            return

    # --- KIỂM TRA 2: SPAM TỐC ĐỘ (RATE LIMIT - Gửi quá 5 tin trong 4 giây) ---
    if user_id not in user_message_timestamps:
        user_message_timestamps[user_id] = []

    # Lọc lại các mốc thời gian trong vòng 4 giây qua
    user_message_timestamps[user_id] = [t for t in user_message_timestamps[user_id] if current_time - t < 4]
    user_message_timestamps[user_id].append(current_time)

    if len(user_message_timestamps[user_id]) > 5:
        try:
            await message.delete()
            # Timeout nhanh 2 phút vì tội spam tốc độ
            import datetime
            await message.author.timeout(datetime.timedelta(minutes=2), reason="AutoMod: Spam tin nhắn quá nhanh")
        except discord.Forbidden:
            pass

        # Xóa bớt list timestamp để tránh spam log liên tục
        user_message_timestamps[user_id].clear()

        await writelogs(
            message.guild, 
            mode="automod", 
            user=message.author, 
            violation="Spam tin nhắn quá nhanh (Rate limit)", 
            content=message.content
        )
        return

    # Cho phép bot tiếp tục xử lý các lệnh khác (nếu có dùng prefix commands)
    await bot.process_commands(message)
# end of the line :)    
TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
