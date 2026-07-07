from __future__ import annotations

import time
from typing import Any

import config
from monitoring_result_4h import MonitorResult
from storage import StoredSignal
from utils import fmt_price


def onoff(value: bool) -> str:
    return "روشن ✅" if value else "خاموش ⛔"


def _duration_text(seconds: int) -> str:
    seconds = max(0, int(seconds))
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, _ = divmod(rem, 60)
    parts: list[str] = []
    if days:
        parts.append(f"{days} روز")
    if hours:
        parts.append(f"{hours} ساعت")
    if minutes or not parts:
        parts.append(f"{minutes} دقیقه")
    return " و ".join(parts)


def render_trade_panel(settings: dict[str, Any], *, active_real: int, free_slots: int, margin_summary: dict[str, Any] | None = None) -> str:
    margin = "نامشخص"
    if margin_summary:
        margin = f"{float(margin_summary.get('available') or margin_summary.get('balance') or 0):.2f} USDT"
    return "\n".join([
        "⚙️ وضعیت ربات",
        "",
        f"✅ اتوسیگنال: {onoff(bool(settings.get('auto_signal_enabled', True)))}",
        f"💹 ترید واقعی: {onoff(bool(settings['real_trade_enabled']))}",
        f"💰 مارجین توبیت: {margin}",
        f"💲 دلار هر پوزیشن: {float(settings['trade_dollar_usdt']):.2f} USDT",
        f"📈 لوریج: {int(settings['leverage'])}x",
        f"🎯 حداکثر پوزیشن: {int(settings['max_positions'])}",
        f"📌 پوزیشن Real فعال: {active_real}",
        f"🟢 اسلات آزاد: {free_slots}",
        f"💵 سرمایه مجاز ربات: {float(settings['trade_capital_usdt']):.2f} USDT",
        f"🧾 کارمزد رفت‌وبرگشت ثابت: {config.ROUND_TRIP_FEE_USDT:.2f} USDT",
        "",
        "📊 تحلیل: OKX",
        "🏦 اجرای واقعی: Toobit Futures",
        "🧱 مارجین: Isolated",
        "⏱ تایم‌فریم اصلی: 4H",
        "",
        "دستورات:",
        "ترید فعال | ترید خاموش",
        "اتوسیگنال فعال | اتوسیگنال خاموش",
        "دلار ترید 10 | لوریج ترید 10 | حداکثر پوزیشن 3",
        "آمار | پوزیشن | کوین‌ها | قوانین",
    ])


def render_signal(signal_id: int, plan: Any, mode: str) -> str:
    d = plan.to_legacy_dict() if hasattr(plan, "to_legacy_dict") else dict(plan)
    title = "🏦 سیگنال توبیت 4H" if mode == "real" else "📊 سیگنال 4H"
    side = "LONG 🟢" if d["direction"] == "LONG" else "SHORT 🔴"
    rr = float(d.get("risk_reward") or 0)
    reasons = d.get("reasons") or []
    reason_lines: list[str] = []
    if isinstance(reasons, (list, tuple)):
        for item in reasons[:8]:
            reason_lines.append(f"• {item}")
    body = [
        title,
        f"#{signal_id} | {d['symbol']}",
        f"جهت: {side}",
        f"امتیاز: {float(d['score']):.1f}/100",
        f"قدرت: {d.get('strength', 'معمولی')}",
        f"RR: {rr:g}",
        "",
        f"Entry: {fmt_price(d['entry_price'])}",
        f"TP: {fmt_price(d['tp_price'])}",
        f"SL 4H: {fmt_price(d['sl_price'])}",
        "",
        f"فاصله TP: {float(d.get('tp_percent') or 0) * 100:.2f}% | فاصله SL: {float(d.get('sl_percent') or 0) * 100:.2f}%",
        f"سود خام تقریبی: {float(d.get('estimated_profit_usdt') or 0):.2f} USDT",
        f"سود خالص تقریبی: {float(d.get('estimated_net_profit_usdt') or 0):.2f} USDT",
        f"کارمزد رفت‌وبرگشت: {float(d.get('round_trip_fee_usdt') or config.ROUND_TRIP_FEE_USDT):.2f} USDT",
    ]
    if reason_lines:
        body.extend(["", "دلایل:", *reason_lines])
    return "\n".join(body)


def render_result(signal: StoredSignal, result: MonitorResult) -> str:
    title = "✅ TP خورد" if result.status == "TP" else "❌ SL خورد" if result.status == "SL" else "ℹ️ خروج/بسته‌شدن"
    source = "🏦 نتیجه توبیت" if signal.signal_type == "real" else "📊 نتیجه سیگنال"
    duration = _duration_text(int(time.time()) - int(signal.opened_at))
    return "\n".join([
        source,
        title,
        f"#{signal.id} | {signal.symbol} | {signal.direction}",
        "",
        f"Entry: {fmt_price(signal.entry_price)}",
        f"Exit: {fmt_price(result.exit_price)}",
        "",
        f"PnL خام: {result.approx_pnl:.2f} USDT",
        f"PnL خالص/واقعی: {result.net_pnl:.2f} USDT",
        "",
        f"حرکت: {result.move_pct * 100:.2f}%",
        f"MFE: {signal.mfe_pct * 100:.2f}% | MAE: {signal.mae_pct * 100:.2f}%",
        f"مدت معامله: {duration}",
        "",
        f"close_reason: {result.reason}",
    ])


def render_stats(stats: dict[str, Any], days: int) -> str:
    normal = stats["normal"]
    real = stats["real"]
    long = stats["long"]
    short = stats["short"]
    failed = stats["real_failed"]
    total_pnl = float(normal["pnl"]) + float(real["pnl"])
    return "\n".join([
        f"📊 آمار {days} روز اخیر",
        "",
        f"💰 سود/ضرر کل: {total_pnl:.2f} USDT",
        "سود/ضرر با کسر کارمزد رفت‌وبرگشت محاسبه شده.",
        "",
        f"🟢 لانگ: سیگنال {long['total']} | TP {long['tp']} | SL {long['sl']} | وین‌ریت {long['win_rate']:.1f}%",
        f"🔴 شورت: سیگنال {short['total']} | TP {short['tp']} | SL {short['sl']} | وین‌ریت {short['win_rate']:.1f}%",
        "",
        "📌 عادی:",
        f"تعداد: {normal['total']} | TP: {normal['tp']} | SL: {normal['sl']} | باز: {normal['open']}",
        f"وین‌ریت: {normal['win_rate']:.1f}% | PnL خالص تقریبی: {normal['pnl']:.2f} USDT",
        "",
        "💰 واقعی:",
        f"تعداد: {real['total']} | TP: {real['tp']} | SL: {real['sl']} | EXIT: {real['exit']} | باز: {real['open']}",
        f"وین‌ریت: {real['win_rate']:.1f}% | PnL واقعی/خالص: {real['pnl']:.2f} USDT",
        f"ارسال واقعی ناموفق: {failed['total']}",
    ])


def render_rules() -> str:
    return "\n".join([
        "📘 قوانین ربات 4H Futures",
        "",
        "1. تحلیل فقط از OKX انجام می‌شود.",
        "2. اجرای واقعی فقط روی Toobit Futures است.",
        "3. مارجین همیشه Isolated است.",
        "4. تایم‌فریم اصلی تحلیل و استاپ 4H است.",
        "5. 1D فقط فیلتر فشار کلی است؛ اگر خلاف 4H باشد معامله رد می‌شود.",
        "6. 1H فقط تریگر ورود است؛ استاپ از 1H گرفته نمی‌شود.",
        "7. ورود داخل رنج ممنوع است.",
        "8. ورود دیر و آخر موج ممنوع است.",
        "9. روی هر ارز فقط یک سیگنال باز مجاز است.",
        "10. RR نسخه اول ثابت 1.5 است.",
        "11. کارمزد رفت‌وبرگشت در PnL لحاظ می‌شود.",
        "12. نتیجه TP/SL با ریپلای روی همان سیگنال ارسال می‌شود.",
        "13. دلار ترید: 1 تا 10000 | لوریج: 1 تا 100 | حداکثر پوزیشن: 1 تا 100.",
        "14. اگر اتوسیگنال خاموش باشد سیگنال جدید ساخته نمی‌شود، ولی پوزیشن‌های باز مانیتور می‌شوند.",
    ])
