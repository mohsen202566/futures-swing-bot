# Futures Hunt Trap Bot

ربات فیوچرز فارسی با منطق **Hidden Pressure Trap Entry**.

## معماری

- OKX: تمام کندل‌ها، قیمت‌ها، تحلیل، سیگنال و مانیتور Normal.
- Toobit: فقط باز کردن پوزیشن واقعی، TP/SL همراه پوزیشن، چک پوزیشن واقعی و PnL واقعی.
- فایل `toobit_client.py` همان فایل ثابت کاربر است و دستکاری نشده است.
- نتیجه هر سیگنال با ریپلای روی پیام اصلی همان سیگنال ارسال می‌شود.
- لاگ‌ها و دلایل رد شدن در SQLite ذخیره می‌شوند و با `cli.py` روی VPS نمایش داده می‌شوند.

## اجرا

```bash
pip install -r requirements.txt
export TELEGRAM_BOT_TOKEN="..."
export TELEGRAM_CHAT_ID="123456"
export TOOBIT_API_KEY="..."
export TOOBIT_API_SECRET="..."
python main.py
```

## دستورات VPS

```bash
python cli.py logs --limit 50
python cli.py logs --level ERROR
python cli.py rejects --limit 50
python cli.py rejects --symbol BTCUSDT
python cli.py stats
python cli.py open
```

## دستورات تلگرام

`ترید`، `پنل`، `وضعیت`، `آمار`، `امروز`، `کوینها`، `لاگ ردها`، `پوزیشن`، `ترید فعال`، `ترید خاموش`، `ترید دلار 10`، `ترید لوریج 10`، `حداکثر پوزیشن 3`، `سرمایه ترید 100`، `حداقل سود خالص 0.01`.


## ساختار نسخه Flat Root
تمام فایل‌های Python این نسخه بدون پوشه و مستقیم در ریشه ریپو قرار گرفته‌اند. فایل `toobit_client.py` همان فایل ثابت کاربر است و تغییر داده نشده است.
