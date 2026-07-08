from __future__ import annotations
class TelegramSender:
    def __init__(self, bot): self.bot=bot
    async def send(self, chat_id:int, text:str): return await self.bot.send_message(chat_id=chat_id,text=text)
    async def reply(self, chat_id:int, message_id:int|None, text:str):
        if message_id:
            try: return await self.bot.send_message(chat_id=chat_id,text=text,reply_to_message_id=int(message_id))
            except Exception: pass
        return await self.bot.send_message(chat_id=chat_id,text=text)
