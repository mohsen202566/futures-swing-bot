from __future__ import annotations
import asyncio
from typing import Any
from telegram.ext import ApplicationBuilder, MessageHandler, filters
import config
from okx_market import OKXMarket
from okx_monitor import OKXMonitor
import log_store, settings_store, signal_store
from database import init_db
from signal_engine import SignalEngine
from symbols import SYMBOLS
from commands import handle_text
from messages import format_result, format_signal
from telegram_bot import TelegramSender
from toobit_client import ToobitClient
from execution_manager import ExecutionManager
from order_verifier import format_real_execution_reply
from result_monitor import ResultMonitor
from slot_manager import SlotManager

class BotRuntime:
    def __init__(self, app):
        self.app=app; self.sender=TelegramSender(app.bot)
        self.okx_market=OKXMarket(); self.signal_engine=SignalEngine(self.okx_market); self.okx_monitor=OKXMonitor(self.okx_market)
        self.toobit=ToobitClient(); self.slot_manager=SlotManager(self.toobit); self.execution=ExecutionManager(self.toobit); self.result_monitor=ResultMonitor(self.okx_monitor,self.toobit)
    async def scanner_loop(self):
        await asyncio.sleep(3)
        while True:
            try:
                if settings_store.get_bool('auto_signal'): await self.scan_once()
            except Exception as exc: log_store.add('ERROR','scanner_loop',f'خطای اسکن: {exc}')
            await asyncio.sleep(config.SCAN_INTERVAL_SECONDS)
    async def scan_once(self):
        for symbol in SYMBOLS:
            if signal_store.has_open_signal(symbol): continue
            sig=self.signal_engine.evaluate(symbol)
            if not sig: continue
            signal_type='Normal'; note='\nوضعیت اجرا: ترید واقعی خاموش است، فقط سیگنال ثبت شد.'
            if settings_store.get_bool('real_trading'):
                can,reason=self.slot_manager.can_open_real(symbol)
                if can: signal_type='Real'; note='\nوضعیت اجرا: ارسال سفارش Real روی Toobit شروع می‌شود.'
                else: note=f'\nوضعیت اجرا: Real فعال است ولی اجرا نشد؛ {reason}. سیگنال Normal ثبت شد.'
            sig['signal_type']=signal_type
            sid=signal_store.add_signal(sig,chat_id=config.TELEGRAM_CHAT_ID)
            msg=await self.sender.send(config.TELEGRAM_CHAT_ID,format_signal(sig,sid,signal_type,note))
            signal_store.update_message_id(sid,config.TELEGRAM_CHAT_ID,msg.message_id)
            log_store.add('SIGNAL','scanner',f'سیگنال {signal_type} ارسال شد',symbol,sig)
            if signal_type=='Real': asyncio.create_task(self._execute_real_and_reply(sid,sig,msg.message_id))
    async def _execute_real_and_reply(self, signal_id:int, sig:dict[str,Any], message_id:int):
        result=await asyncio.to_thread(self.execution.execute_real,signal_id,sig)
        await self.sender.reply(config.TELEGRAM_CHAT_ID,message_id,format_real_execution_reply(result))
    async def monitor_loop(self):
        await asyncio.sleep(10)
        while True:
            try:
                for row in signal_store.get_open_signals():
                    res=self.result_monitor.check_signal(row)
                    if res:
                        updated=signal_store.get_signal(int(row['id'])) or row
                        await self.sender.reply(int(updated.get('telegram_chat_id') or config.TELEGRAM_CHAT_ID),updated.get('telegram_message_id'),format_result(updated,res))
                        log_store.add('RESULT','monitor',f"نتیجه {res['result']} ثبت شد",row['symbol'],res)
            except Exception as exc: log_store.add('ERROR','monitor_loop',f'خطای مانیتور: {exc}')
            await asyncio.sleep(config.MONITOR_INTERVAL_SECONDS)

async def post_init(app):
    runtime=BotRuntime(app); app.bot_data['runtime']=runtime
    asyncio.create_task(runtime.scanner_loop()); asyncio.create_task(runtime.monitor_loop())

def main():
    init_db(); settings_store.ensure_defaults()
    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID: raise RuntimeError('TELEGRAM_BOT_TOKEN و TELEGRAM_CHAT_ID باید تنظیم شوند.')
    app=ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).post_init(post_init).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    log_store.add('INFO','main','ربات شروع شد')
    app.run_polling(close_loop=False)
if __name__=='__main__': main()
