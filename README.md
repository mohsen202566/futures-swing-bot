# Futures Hunt Trap Bot

ربات فیوچرز فارسی با منطق **Hidden Pressure Trap Entry**.

## معماری

- OKX: تمام کندل‌ها، قیمت‌ها، تحلیل، سیگنال و مانیتور Normal.
- Toobit: فقط باز کردن پوزیشن واقعی، TP/SL همراه پوزیشن، چک پوزیشن واقعی و PnL واقعی.
- فایل `toobit_client.py` همان فایل ثابت کاربر است و دستکاری نشده است.
- نتیجه هر سیگنال با ریپلای روی پیام اصلی همان سیگنال ارسال می‌شود.
- لاگ‌ها و دلایل رد شدن در SQLite ذخیره می‌شوند و با `cli.py` روی VPS نمایش داده می‌شوند.

## اجرا

ربات فایل‌های `.env`، `env`، `config.env` یا `bot.env` را از ریشه پروژه خودش می‌خواند. مقدارها را داخل یکی از این فایل‌ها بگذارید، ولی آن فایل را داخل GitHub عمومی نگذارید.

نام متغیرهای سازگار با تنظیمات فعلی:

```bash
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=1055122209
OWNER_ID=1055122209
TOOBIT_API_KEY=...
TOOBIT_API_SECRET=...
DEFAULT_TRADE_ENABLED=0
DEFAULT_TRADE_DOLLAR=10
DEFAULT_LEVERAGE=10
DEFAULT_MAX_POSITIONS=3
ROUND_TRIP_FEE_USDT=0.05
BOT_NAME=Crypto 4H Trend Pullback Toobit Bot
BOT_DATA_DIR=data
BOT_DB_PATH=data/crypto_4h_trend_pullback.sqlite3
```

اجرای ربات:

```bash
cd /opt/crypto_4h_bot
source venv/bin/activate
pip install -r requirements.txt
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
