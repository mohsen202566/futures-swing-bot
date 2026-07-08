from __future__ import annotations
import rejection_store, settings_store, signal_store, stats_manager
from messages import format_rejections
from panels import symbols_panel, trade_panel
from toobit_client import ToobitClient

def _num_after(text,prefix):
    return text[len(prefix):].strip() if text.strip().startswith(prefix) and text[len(prefix):].strip() else None
async def handle_text(update, context):
    text=(update.message.text or '').strip(); toobit=ToobitClient()
    if text in {'ترید','پنل','وضعیت','راهنما'}:
        bal={}
        try: bal=toobit.get_usdt_balance_summary()
        except Exception: pass
        await update.message.reply_text(trade_panel(bal)); return
    if text=='ترید فعال': settings_store.set_value('real_trading',True); await update.message.reply_text('✅ ترید واقعی فعال شد.'); return
    if text=='ترید خاموش': settings_store.set_value('real_trading',False); await update.message.reply_text('⛔ ترید واقعی خاموش شد.'); return
    v=_num_after(text,'ترید دلار')
    if v: settings_store.set_value('margin_per_position',float(v)); await update.message.reply_text(f'✅ دلار هر پوزیشن تنظیم شد: {float(v):.2f} USDT'); return
    v=_num_after(text,'ترید لوریج')
    if v: settings_store.set_value('leverage',int(float(v))); await update.message.reply_text(f'✅ لوریج تنظیم شد: {int(float(v))}x'); return
    v=_num_after(text,'حداکثر پوزیشن')
    if v: settings_store.set_value('max_real_positions',int(float(v))); await update.message.reply_text(f'✅ حداکثر پوزیشن تنظیم شد: {int(float(v))}'); return
    v=_num_after(text,'سرمایه ترید')
    if v: settings_store.set_value('capital_limit',float(v)); await update.message.reply_text(f'✅ سرمایه مجاز ربات تنظیم شد: {float(v):.2f} USDT'); return
    v=_num_after(text,'حداقل سود خالص')
    if v: settings_store.set_value('min_net_profit',float(v)); await update.message.reply_text(f'✅ حداقل سود خالص تنظیم شد: {float(v):.2f} USDT'); return
    if text.startswith('آمار'): await update.message.reply_text(stats_manager.format_stats(30)); return
    if text=='امروز': await update.message.reply_text(stats_manager.format_stats(1)); return
    if text=='کوینها': await update.message.reply_text(symbols_panel()); return
    if text=='حذف آمار': signal_store.reset_stats_only(); await update.message.reply_text('✅ آمار بسته‌شده‌ها آرشیو شد.'); return
    if text.startswith('لاگ ردها'):
        parts=text.split(); symbol=parts[2] if len(parts)>=3 else None
        await update.message.reply_text(format_rejections(rejection_store.list_rejections(limit=20,symbol=symbol))); return
    if text=='پوزیشن':
        try:
            ps=toobit.get_positions(); await update.message.reply_text('پوزیشن واقعی باز پیدا نشد.' if not ps else '📌 پوزیشن‌های Toobit:\n'+'\n'.join(str(p)[:300] for p in ps[:10]))
        except Exception as exc: await update.message.reply_text(f'خطا در خواندن پوزیشن: {exc}')
        return
    await update.message.reply_text('دستور شناخته نشد. دستور «ترید» را بفرست.')
