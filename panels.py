from __future__ import annotations
import settings_store, signal_store
from symbols import SYMBOLS

def trade_panel(balance:dict|None=None)->str:
    s=settings_store.snapshot(); balance=balance or {}; real_on='فعال ✅' if s['real_trading']=='1' else 'خاموش ⛔'; auto='فعال ✅' if s['auto_signal']=='1' else 'خاموش ⛔'
    max_pos=int(float(s['max_real_positions'])); open_real=signal_store.count_real_open(); free=max(0,max_pos-open_real)
    return (f"⚙️ وضعیت ربات Hidden Trap 5M/15M\n\n💹 ترید واقعی: {real_on}\n📡 اتو سیگنال: {auto}\n\n📊 منبع دیتا و تحلیل: OKX\n🎯 مانیتور Normal: OKX\n💸 اجرای Real: Toobit\n📌 چک پوزیشن Real: Toobit\n\n💰 مارجین توبیت: {float(balance.get('available') or 0):.2f} USDT\n💵 دلار هر پوزیشن: {float(s['margin_per_position']):.2f} USDT\n📈 لوریج: {int(float(s['leverage']))}x\n🎯 حداکثر پوزیشن: {max_pos}\n📌 پوزیشن Real فعال: {open_real}\n🟢 اسلات آزاد: {free}\n🧾 کارمزد رفت‌وبرگشت ثابت: {float(s['fixed_fee']):.2f} USDT\n✅ حداقل سود خالص: {float(s['min_net_profit']):.2f} USDT\n📐 RR: 1.5\n🎯 ورود: Hidden Pressure Trap\n🪤 TP/SL Real: همراه پوزیشن Toobit\n⏱ چک پوزیشن Real: 70 ثانیه بعد از ارسال\n\nدستورات:\nترید فعال | ترید خاموش\nترید دلار 10 | ترید لوریج 10 | حداکثر پوزیشن 3\nسرمایه ترید 100 | حداقل سود خالص 0.01\nآمار | کوینها | پوزیشن | لاگ ردها | وضعیت")
def symbols_panel()->str: return '🪙 لیست ثابت ۳۰ ارز:\n'+'\n'.join(f'{i+1}. {s}' for i,s in enumerate(SYMBOLS))
