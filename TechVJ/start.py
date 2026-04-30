# Don't Remove Credit Tg - @VJ_Bots
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01

import os
import asyncio 
import pyrogram
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated, UserAlreadyParticipant, InviteHashExpired, UsernameNotOccupied
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message 

from config import API_ID, API_HASH, ERROR_MESSAGE, LOGIN_SYSTEM, STRING_SESSION, CHANNEL_ID, WAITING_TIME
from database.db import db
from TechVJ.strings import HELP_TXT
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

# ======== BATCH & PROGRESS TRACKER ========
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

def progress(current, total, message, type_):
    if total == 0: total = 1
    percent = current * 100 / total
    done = int(percent / 10)
    bar = "█" * done + "░" * (10 - done)
    c_size = format_bytes(current)
    t_size = format_bytes(total)
    
    text = f"**{percent:.2f}%**\n`{bar}`\n**Size:** `{c_size} / {t_size}`"
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
            
            msg_text = (
                f"📥 **Downloading...**\n"
                f"{txt}\n\n"
                f"📊 **Batch Status:**\n"
                f"🔹 Total: `{t_total}`  |  ⏳ Rem: `{t_rem}`\n"
                f"✅ Done: `{t_comp}`  |  ❌ Fail: `{t_fail}`"
            )
            await client.edit_message_text(chat, smsg.id, msg_text)
            await asyncio.sleep(5)
        except Exception:
            await asyncio.sleep(5)

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
            
            msg_text = (
                f"📤 **Uploading...**\n"
                f"{txt}\n\n"
                f"📊 **Batch Status:**\n"
                f"🔹 Total: `{t_total}`  |  ⏳ Rem: `{t_rem}`\n"
                f"✅ Done: `{t_comp}`  |  ❌ Fail: `{t_fail}`"
            )
            await client.edit_message_text(chat, smsg.id, msg_text)
            await asyncio.sleep(5)
        except Exception:
            await asyncio.sleep(5)
# ==========================================


@Client.on_message(filters.command(["start"]))
async def send_start(client: Client, message: Message):
    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.first_name)
    buttons = [[
        InlineKeyboardButton("❣️ Developer", url = "https://t.me/kingvj01")
    ],[
        InlineKeyboardButton('🔍 sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ', url='https://t.me/vj_bot_disscussion'),
        InlineKeyboardButton('🤖 ᴜᴘᴅᴀᴛᴇ ᴄʜᴀɴɴᴇʟ', url='https://t.me/vj_bots')
    ]]
    reply_markup = InlineKeyboardMarkup(buttons)
    await client.send_message(
        chat_id=message.chat.id, 
        text=f"<b>👋 Hi {message.from_user.mention}, I am Save Restricted Content Bot (PREMIUM VERSION ✨). I can send you restricted content by its post link.\n\nFor downloading restricted content /login first.\n\nKnow how to use bot by - /help</b>", 
        reply_markup=reply_markup, 
        reply_to_message_id=message.id
    )

@Client.on_message(filters.command(["help"]))
async def send_help(client: Client, message: Message):
    await client.send_message(chat_id=message.chat.id, text=f"{HELP_TXT}")

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

@Client.on_message(filters.text & filters.private & ~filters.command(["start", "help", "cancel", "setchannel", "delchannel"]) & ~filters.forwarded)
async def save(client: Client, message: Message):
    if ("https://t.me/+" in message.text or "https://t.me/joinchat/" in message.text) and LOGIN_SYSTEM == False:
        if TechVJUser is None:
            await client.send_message(message.chat.id, "String Session is not Set", reply_to_message_id=message.id)
            return
        try:
            try: await TechVJUser.join_chat(message.text)
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
        
        # Batch Data Init
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
                        if msg.empty: is_success = False
                        else:
                            custom_channel = await get_user_channel(message.chat.id)
                            target_chat = custom_channel if custom_channel else (int(CHANNEL_ID) if CHANNEL_ID else message.chat.id)
                            await client.copy_message(target_chat, msg.chat.id, msg.id, reply_to_message_id=message.id)
                            is_success = True
                    except UsernameNotOccupied: 
                        await client.send_message(message.chat.id, "The username is not occupied by anyone", reply_to_message_id=message.id)
                        is_success = False
                    except Exception:
                        try:    
                            is_success = await handle_private(client, acc, message, username, msgid)               
                        except Exception as e:
                            is_success = False
            except Exception as e:
                is_success = False

            # Update Batch Progress
            if is_success:
                BATCH_DATA[message.from_user.id]["completed"] += 1
            else:
                BATCH_DATA[message.from_user.id]["failed"] += 1

            await asyncio.sleep(WAITING_TIME)
            
        if LOGIN_SYSTEM == True:
            try: await acc.disconnect()
            except: pass                				
        
        # Final Completion Message
        if not batch_temp.IS_BATCH.get(message.from_user.id) and total_tasks > 1:
            t_total = BATCH_DATA[message.from_user.id]["total"]
            t_comp = BATCH_DATA[message.from_user.id]["completed"]
            t_fail = BATCH_DATA[message.from_user.id]["failed"]
            await message.reply_text(f"🎉 **Batch Processing Completed!**\n\n🔹 Total Tasks: `{t_total}`\n✅ Completed: `{t_comp}`\n❌ Failed: `{t_fail}`")

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
    
    try:
        file = await acc.download_media(msg, progress=progress, progress_args=[message,"down"])
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
    try:
        if "Document" == msg_type:
            try: ph_path = await acc.download_media(msg.document.thumbs[0].file_id)
            except: ph_path = None
            await client.send_document(chat, file, thumb=ph_path, caption=caption, reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML, progress=progress, progress_args=[message,"up"])
            if ph_path != None: os.remove(ph_path)
            is_success = True
            
        elif "Video" == msg_type:
            try: ph_path = await acc.download_media(msg.video.thumbs[0].file_id)
            except: ph_path = None
            await client.send_video(chat, file, duration=msg.video.duration, width=msg.video.width, height=msg.video.height, thumb=ph_path, caption=caption, reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML, progress=progress, progress_args=[message,"up"])
            if ph_path != None: os.remove(ph_path)
            is_success = True

        elif "Animation" == msg_type:
            await client.send_animation(chat, file, reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)
            is_success = True
            
        elif "Sticker" == msg_type:
            await client.send_sticker(chat, file, reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)
            is_success = True

        elif "Voice" == msg_type:
            await client.send_voice(chat, file, caption=caption, caption_entities=msg.caption_entities, reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML, progress=progress, progress_args=[message,"up"])
            is_success = True

        elif "Audio" == msg_type:
            try: ph_path = await acc.download_media(msg.audio.thumbs[0].file_id)
            except: ph_path = None
            await client.send_audio(chat, file, thumb=ph_path, caption=caption, reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML, progress=progress, progress_args=[message,"up"])   
            if ph_path != None: os.remove(ph_path)
            is_success = True

        elif "Photo" == msg_type:
            await client.send_photo(chat, file, caption=caption, reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)
            is_success = True

    except Exception as e:
        if ERROR_MESSAGE == True:
            await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)
        is_success = False

    if os.path.exists(f'{message.id}upstatus.txt'): 
        os.remove(f'{message.id}upstatus.txt')
    if file and os.path.exists(file):
        os.remove(file)
    await client.delete_messages(message.chat.id,[smsg.id])
    return is_success

def get_message_type(msg: pyrogram.types.messages_and_media.message.Message):
    try: msg.document.file_id; return "Document"
    except: pass
    try: msg.video.file_id; return "Video"
    except: pass
    try: msg.animation.file_id; return "Animation"
    except: pass
    try: msg.sticker.file_id; return "Sticker"
    except: pass
    try: msg.voice.file_id; return "Voice"
    except: pass
    try: msg.audio.file_id; return "Audio"
    except: pass
    try: msg.photo.file_id; return "Photo"
    except: pass
    try: msg.text; return "Text"
    except: pass
