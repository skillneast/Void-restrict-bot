# Don't Remove Credit Tg - @VJ_Bots
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01

from pyrogram import Client, filters
from config import API_ID, API_HASH, BOT_TOKEN, STRING_SESSION, LOGIN_SYSTEM, DB_URI
from motor.motor_asyncio import AsyncIOMotorClient

# ================= MONGODB SETUP =================
# MongoDB connect kar rahe hain taaki data restart ke baad bhi save rahe
db_client = AsyncIOMotorClient(DB_URI)
db = db_client["VJ_Bot_DB"]
user_data = db["custom_channels"]

async def set_user_channel(user_id, channel_id):
    await user_data.update_one({"user_id": user_id}, {"$set": {"channel_id": channel_id}}, upsert=True)

async def del_user_channel(user_id):
    await user_data.delete_one({"user_id": user_id})
# =================================================

if STRING_SESSION is not None and LOGIN_SYSTEM == False:
	TechVJUser = Client("TechVJ", api_id=API_ID, api_hash=API_HASH, session_string=STRING_SESSION)
	TechVJUser.start()
else:
    TechVJUser = None

class Bot(Client):

    def __init__(self):
        super().__init__(
            "techvj login",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            plugins=dict(root="TechVJ"),
            workers=150,
            sleep_threshold=5
        )

      
    async def start(self):
        await super().start()
        print('Bot Started Powered By @VJ_Bots')

    async def stop(self, *args):
        await super().stop()
        print('Bot Stopped Bye')

bot = Bot()

# ============ CUSTOM CHANNEL COMMANDS ============
WAIT_FOR_FORWARD = {}

@bot.on_message(filters.command("setchannel") & filters.private)
async def set_channel_cmd(client, message):
    WAIT_FOR_FORWARD[message.chat.id] = True
    await message.reply_text(
        "Apne naye channel se koi bhi ek message yahan forward karo.\n\n"
        "(⚠️ Dhyaan rahe: Message forward karne se pehle bot ko us channel me Admin zaroor bana dena!)"
    )

@bot.on_message(filters.private & filters.forwarded)
async def catch_forward(client, message):
    if WAIT_FOR_FORWARD.get(message.chat.id):
        if message.forward_from_chat:
            channel_id = message.forward_from_chat.id
            # User ka channel MongoDB me permanently save ho raha hai
            await set_user_channel(message.chat.id, channel_id)
            WAIT_FOR_FORWARD[message.chat.id] = False
            
            await message.reply_text(
                f"✅ Aapka custom channel set ho gaya hai!\n\n"
                f"**Channel ID:** `{channel_id}`\n\n"
                f"📁 Database me save ho gaya hai. Bot restart hone par bhi reset nahi hoga."
            )
        else:
            await message.reply_text("❌ Ye message kisi channel se forward nahi kiya gaya hai ya us channel ki privacy hidden hai. Dobara try karein.")

@bot.on_message(filters.command("delchannel") & filters.private)
async def del_channel_cmd(client, message):
    await del_user_channel(message.chat.id)
    await message.reply_text("✅ Aapka custom channel database se hata diya gaya hai. Ab files aapke pehle wale Default channel me aayengi.")
# =================================================

if __name__ == "__main__":
    bot.run()
