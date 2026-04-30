# Don't Remove Credit Tg - @VJ_Bots
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01

import os
import asyncio 
import pyrogram
import time
import math
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated, UserAlreadyParticipant, InviteHashExpired, UsernameNotOccupied
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message 

from config import API_ID, API_HASH, ERROR_MESSAGE, LOGIN_SYSTEM, STRING_SESSION, CHANNEL_ID, WAITING_TIME
from database.db import db
from bot import TechVJUser

# ======= MONGODB CUSTOM CHANNEL SETUP =======
WAIT_FOR_FORWARD = {}

import config
DB_URI = getattr(config, "DB_URI", os.environ.get("DB_URI", None))

try:
    from motor.motor_asyncio import AsyncIOMotorClient
    if not DB_URI:
        raise Exception("DB_URI missing")
        
    db_client = AsyncIOMotorClient(DB_URI)
    custom_db = db_client["VJ_Bot_DB"]
    custom_channels_col = custom_db["custom_channels"]

    async def set_user_channel(user_id, channel_id):
        await custom_channels_col.update_one({"user_id": user_id}, {"$set": {"channel_id": channel_id}}, upsert=True)

    async def del_user_channel(user_id):
        await custom_channels_col.delete_one({"user_id": user_id})

    async def get_user_channel(user_id):
        doc = await custom_channels_col.find_one({"user_id": user_id})
        return doc["channel_id"] if doc else None
except Exception as e:
    user_channels = {}
    async def set_user_channel(user_id, channel_id): user_channels[user_id] = channel_id
    async def del_user_channel(user_id):
        if user_id in user_channels: del user_channels[user_id]
    async def get_user_channel(user_id): return user_channels.get(user_id, None)
# ============================================

# ======== PROGRESS BAR & BATCH TRACKER ========
BATCH_DATA = {}

class batch_temp(object):
    IS_BATCH = {}

def format_bytes(size):
    power = 1024
    n = 0
    power_labels = {0: 'B', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}
    while size > power and n < 4:
        size /= power
        n += 1
    return f"{size:.2f} {power_labels[n]}"

def get_readable_time(seconds):
    count = 0
    ping_time = ""
    time_list =[]
    time_suffix_list = ["s", "m", "h", "days"]
    while count < 4:
        count += 1
        remainder, result = divmod(seconds, 60) if count < 3 else divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)
    for x in range(len(time_list)):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        ping_time += time_list.pop() + ", "
    time_list.reverse()
    ping_time += ":".join(time_list)
    return ping_time if ping_time else "0s"

def progress(current, total, message, type_, start_time):
    now = time.time()
    diff = now - start_time
    if diff == 0: diff = 1
    if total == 0: total = 1
    
    percent = current * 100 / total
    done = math.floor(percent / 10)
    bar = "█" * done + "░" * (10 - done)
    
    speed = current / diff
    c_size = format_bytes(current)
    t_size = format_bytes(total)
    speed_str = format_bytes(speed) + "/s"
    
    eta = (total - current) / speed if speed > 0 else 0
    eta_str = get_readable_time(eta)
    
    text = f"**{percent:.2f}%**\n`[{bar}]`\n📦 **Size:** `{c_size} / {t_size}`\n🚀 **Speed:** `{speed_str}`\n⏳ **ETA:** `{eta_str}`"
    
    with open(f'{message.id}{type_}status.txt', "w", encoding="utf-8") as fileup:
        fileup.write(text)

async def downstatus(client, statusfile, smsg, chat, user_id):
    while True:
        if os.path.exists(statusfile): break
        await asyncio.sleep(3)
      
    while os.path.exists(statusfile):
        try:
            with open(statusfile, "r", encoding="utf-8") as downread:
                txt = downread.read()
            
            batch = BATCH_DATA.get(user_id, {})
            t_total = batch.get("total", 1)
            t_comp = batch.get("completed", 0)
            t_fail = batch.get("failed", 0)
            t_rem = t_total - t_comp - t_fail
            
            batch_text = ""
            if t_total > 1:
                batch_text = (
                    f"\n\n📊 **Batch Status:**\n"
                    f"🔹 **Total:** `{t_total}`  |  ⏳ **Rem:** `{t_rem}`\n"
                    f"✅ **Done:** `{t_comp}`  |  ❌ **Fail:** `{t_fail}`"
                )
            
            msg_text = f"📥 **Downloading...**\n\n{txt}{batch_text}"
            await client.edit_message_text(chat, smsg.id, msg_text)
            await asyncio.sleep(4)
        except Exception:
            await asyncio.sleep(4)

async def upstatus(client, statusfile, smsg, chat, user_id):
    while True:
        if os.path.exists(statusfile): break
        await asyncio.sleep(3)      
    while os.path.exists(statusfile):
        try:
            with open(statusfile, "r", encoding="utf-8") as upread:
                txt = upread.read()
            
            batch = BATCH_DATA.get(user_id, {})
            t_total = batch.get("total", 1)
            t_comp = batch.get("completed", 0)
            t_fail = batch.get("failed", 0)
            t_rem = t_total - t_comp - t_fail
            
            batch_text = ""
            if t_total > 1:
                batch_text = (
                    f"\n\n📊 **Batch Status:**\n"
                    f"🔹 **Total:** `{t_total}`  |  ⏳ **Rem:** `{t_rem}`\n"
                    f"✅ **Done:** `{t_comp}`  |  ❌ **Fail:** `{t_fail}`"
                )
            
            msg_text = f"📤 **Uploading...**\n\n{txt}{batch_text}"
            await client.edit_message_text(chat, smsg.id, msg_text)
            await asyncio.sleep(4)
        except Exception:
            await asyncio.sleep(4)
# ==========================================


# ================= COMMANDS =================
@Client.on_message(filters.command(["start"]))
async def send_start(client: Client, message: Message):
    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.first_name)
    
    buttons = [[
        InlineKeyboardButton("❣️ Developer", url="https://t.me/skillneast")
    ],[
        InlineKeyboardButton('🌟 OG Channel', url='https://t.me/skillneastreal'),
        InlineKeyboardButton('🤖 Update Channel', url='https://t.me/skillneast')
    ]]
    reply_markup = InlineKeyboardMarkup(buttons)
    
    start_text = f"""<b>👋 Hello {message.from_user.mention}!

I am an Advanced Save Restricted Content Bot (PREMIUM ✅).
I can help you extract and save restricted content from private channels and groups.

🌟 Main Features:
• Custom Dump Channel support.
• Advanced Batch downloading support.
• Animated Progress & Speed tracking.
• Login via Session to access private chats.

Check /help to see all available commands!</b>"""

    await client.send_message(
        chat_id=message.chat.id, 
        text=start_text, 
        reply_markup=reply_markup, 
        reply_to_message_id=message.id
    )

@Client.on_message(filters.command(["help"]))
async def send_help(client: Client, message: Message):
    help_text = """<b>🛠 Available Commands & Features:

/start - Check if the bot is alive and working.
/help - Show this help message with all command details.
/login - Login with your Telegram session to download from private/restricted channels.
/logout - Remove your logged-in session.
/setchannel - Set a Custom Dump Channel. Forward a message from your channel to the bot, and all extracted files will be sent there. (Make sure Bot is Admin in that channel).
/delchannel - Remove your Custom Dump Channel and save files to the default location.
/batch - Learn how to download multiple posts at once (Batch Download).
/cancel - Cancel any ongoing batch downloading process.

📥 How to download:
Just send the Telegram message link!
Example: <code>https://t.me/channelname/101</code></b>"""
    await client.send_message(chat_id=message.chat.id, text=help_text)

@Client.on_message(filters.command(["batch"]))
async def send_batch_info(client: Client, message: Message):
    batch_text = """<b>📦 How to use Batch Download Feature:

You can download multiple files at once by sending a link with a range!

Format:
<code>https://t.me/channelname/100-110</code>

Instructions:
1. Copy the link of the FIRST post (e.g., ID 100).
2. Add a hyphen <code>-</code> followed by the ID of the LAST post (e.g., ID 110).
3. Send it to the bot.

⚠️ Note:
• Make sure there are NO spaces between the numbers.
• Do not request too many files at once (e.g., 1000 files) to avoid FloodWait ban. Try 10-20 files at a time.</b>"""
    await client.send_message(chat_id=message.chat.id, text=batch_text)

@Client.on_message(filters.command(["cancel"]))
async def send_cancel(client: Client, message: Message):
    batch_temp.IS_BATCH[message.from_user.id] = True
    await client.send_message(chat_id=message.chat.id, text="**Batch Successfully Cancelled.**")


# ======= CUSTOM CHANNEL COMMANDS =======
@Client.on_message(filters.command(["setchannel"]) & filters.private, group=-1)
async def set_channel_cmd(client: Client, message: Message):
    WAIT_FOR_FORWARD[message.chat.id] = True
    await message.reply_text(
        "<b>Please forward a message from your channel.</b>\n\n"
        "(Make sure the bot is an Admin in that channel first!)"
    )
    message.stop_propagation()

@Client.on_message(filters.private & filters.forwarded, group=-1)
async def catch_forward(client: Client, message: Message):
    if WAIT_FOR_FORWARD.get(message.chat.id):
        if message.forward_from_chat:
            channel_id = message.forward_from_chat.id
            await set_user_channel(message.chat.id, channel_id)
            WAIT_FOR_FORWARD[message.chat.id] = False
            await message.reply_text(
                f"✅ **Channel is set successfully!**\n\n"
                f"**Channel ID:** `{channel_id}`\n"
                f"All files will now be saved in this channel."
            )
        else:
            await message.reply_text("❌ This is not a valid channel forward. The channel might be restricted or privacy is hidden. Please try again.")
        message.stop_propagation()

@Client.on_message(filters.command(["delchannel"]) & filters.private, group=-1)
async def del_channel_cmd(client: Client, message: Message):
    await del_user_channel(message.chat.id)
    await message.reply_text("✅ **Channel is deleted!**\nFiles will now be saved in the default channel.")
    message.stop_propagation()
# ========================================

@Client.on_message(filters.text & filters.private & ~filters.command(["start", "help", "cancel", "setchannel", "delchannel", "batch"]) & ~filters.forwarded)
async def save(client: Client, message: Message):
    if ("https://t.me/+" in message.text or "https://t.me/joinchat/" in message.text) and LOGIN_SYSTEM == False:
        if TechVJUser is None:
            await client.send_message(message.chat.id, "String Session is not Set", reply_to_message_id=message.id)
            return
        try:
            try:
                await TechVJUser.join_chat(message.text)
            except Exception as e: 
                await client.send_message(message.chat.id, f"Error : {e}", reply_to_message_id=message.id)
                return
            await client.send_message(message.chat.id, "Chat Joined", reply_to_message_id=message.id)
        except UserAlreadyParticipant:
            await client.send_message(message.chat.id, "Chat already Joined", reply_to_message_id=message.id)
        except InviteHashExpired:
            await client.send_message(message.chat.id, "Invalid Link", reply_to_message_id=message.id)
        return
    
    if "https://t.me/" in message.text:
        if batch_temp.IS_BATCH.get(message.from_user.id) == False:
            return await message.reply_text("**One Task Is Already Processing. Wait For Complete It. If You Want To Cancel This Task Then Use - /cancel**")
        datas = message.text.split("/")
        temp = datas[-1].replace("?single","").split("-")
        fromID = int(temp[0].strip())
        try: toID = int(temp[1].strip())
        except: toID = fromID

        if LOGIN_SYSTEM == True:
            user_data = await db.get_session(message.from_user.id)
            if user_data is None:
                await message.reply("**For Downloading Restricted Content You Have To /login First.**")
                return
            api_id = int(await db.get_api_id(message.from_user.id))
            api_hash = await db.get_api_hash(message.from_user.id)
            try:
                acc = Client("saverestricted", session_string=user_data, api_hash=api_hash, api_id=api_id)
                await acc.connect()
            except:
                return await message.reply("**Your Login Session Expired. So /logout First Then Login Again By - /login**")
        else:
            if TechVJUser is None:
                await client.send_message(message.chat.id, f"**String Session is not Set**", reply_to_message_id=message.id)
                return
            acc = TechVJUser
				
        batch_temp.IS_BATCH[message.from_user.id] = False
        
        # Batch Data Initialization
        total_tasks = toID - fromID + 1
        BATCH_DATA[message.from_user.id] = {"total": total_tasks, "completed": 0, "failed": 0}

        for msgid in range(fromID, toID+1):
            if batch_temp.IS_BATCH.get(message.from_user.id): break
            
            is_success = False
            try:
                if "https://t.me/c/" in message.text:
                    chatid = int("-100" + datas[4])
                    is_success = await handle_private(client, acc, message, chatid, msgid)
    
                elif "https://t.me/b/" in message.text:
                    username = datas[4]
                    is_success = await handle_private(client, acc, message, username, msgid)
                
                else:
                    username = datas[3]
                    try:
                        msg = await client.get_messages(username, msgid)
                        if msg.empty: 
                            is_success = False
                        else:
                            custom_channel = await get_user_channel(message.chat.id)
                            target_chat = custom_channel if custom_channel else (int(CHANNEL_ID) if CHANNEL_ID else message.chat.id)
                            await client.copy_message(target_chat, msg.chat.id, msg.id, reply_to_message_id=message.id)
                            is_success = True
                    except UsernameNotOccupied: 
                        await client.send_message(message.chat.id, "The username is not occupied by anyone", reply_to_message_id=message.id)
                        is_success = False
                    except Exception:
                        try: is_success = await handle_private(client, acc, message, username, msgid)               
                        except: is_success = False
            except:
                is_success = False

            # Update Tracker
            if is_success: BATCH_DATA[message.from_user.id]["completed"] += 1
            else: BATCH_DATA[message.from_user.id]["failed"] += 1

            await asyncio.sleep(WAITING_TIME)
            
        if LOGIN_SYSTEM == True:
            try: await acc.disconnect()
            except: pass                				
        
        # Final Summary for Batch
        if not batch_temp.IS_BATCH.get(message.from_user.id) and total_tasks > 1:
            t_total = BATCH_DATA[message.from_user.id]["total"]
            t_comp = BATCH_DATA[message.from_user.id]["completed"]
            t_fail = BATCH_DATA[message.from_user.id]["failed"]
            await message.reply_text(
                f"🎉 **Batch Processing Completed!**\n\n"
                f"🔹 **Total Tasks:** `{t_total}`\n"
                f"✅ **Successful:** `{t_comp}`\n"
                f"❌ **Failed:** `{t_fail}`"
            )

        batch_temp.IS_BATCH[message.from_user.id] = True


async def handle_private(client: Client, acc, message: Message, chatid: int, msgid: int):
    try:
        msg: Message = await acc.get_messages(chatid, msgid)
        if msg.empty: return False
    except Exception:
        return False
        
    msg_type = get_message_type(msg)
    if not msg_type: return False 

    custom_channel = await get_user_channel(message.chat.id)
    chat = custom_channel if custom_channel else (int(CHANNEL_ID) if CHANNEL_ID else message.chat.id)

    if batch_temp.IS_BATCH.get(message.from_user.id): return False
    if "Text" == msg_type:
        try:
            await client.send_message(chat, msg.text, entities=msg.entities, reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)
            return True
        except Exception as e:
            if ERROR_MESSAGE == True:
                await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)
            return False 

    smsg = await client.send_message(message.chat.id, '**Downloading...**', reply_to_message_id=message.id)
    asyncio.create_task(downstatus(client, f'{message.id}downstatus.txt', smsg, message.chat.id, message.from_user.id)) 
    
    start_time = time.time()
    try:
        file = await acc.download_media(msg, progress=progress, progress_args=[message,"down", start_time])
        if os.path.exists(f'{message.id}downstatus.txt'): os.remove(f'{message.id}downstatus.txt')
    except Exception as e:
        if ERROR_MESSAGE == True:
            await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML) 
        await smsg.delete()
        return False

    if batch_temp.IS_BATCH.get(message.from_user.id): return False 
    asyncio.create_task(upstatus(client, f'{message.id}upstatus.txt', smsg, message.chat.id, message.from_user.id))

    caption = msg.caption if msg.caption else None
    if batch_temp.IS_BATCH.get(message.from_user.id): return False 
            
    is_success = False
    start_time = time.time()
    try:
        if "Document" == msg_type:
            try: ph_path = await acc.download_media(msg.document.thumbs[0].file_id)
            except: ph_path = None
            await client.send_document(chat, file, thumb=ph_path, caption=caption, reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML, progress=progress, progress_args=[message,"up", start_time])
            if ph_path != None: os.remove(ph_path)
            is_success = True
            
        elif "Video" == msg_type:
            try: ph_path = await acc.download_media(msg.video.thumbs[0].file_id)
            except: ph_path = None
            await client.send_video(chat, file, duration=msg.video.duration, width=msg.video.width, height=msg.video.height, thumb=ph_path, caption=caption, reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML, progress=progress, progress_args=[message,"up", start_time])
            if ph_path != None: os.remove(ph_path)
            is_success = True

        elif "Animation" == msg_type:
            await client.send_animation(chat, file, reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)
            is_success = True
            
        elif "Sticker" == msg_type:
            await client.send_sticker(chat, file, reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)
            is_success = True

        elif "Voice" == msg_type:
            await client.send_voice(chat, file, caption=caption, caption_entities=msg.caption_entities, reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML, progress=progress, progress_args=[message,"up", start_time])
            is_success = True

        elif "Audio" == msg_type:
            try: ph_path = await acc.download_media(msg.audio.thumbs[0].file_id)
            except: ph_path = None
            await client.send_audio(chat, file, thumb=ph_path,
