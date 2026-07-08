from __future__ import annotations

def format_real_execution_reply(result:dict)->str:
    if result.get('opened'):
        return f"✅ پوزیشن واقعی تایید شد\nOrder ID: {result.get('order_id') or '-'}\nEntry: {result.get('entry_price')}\nTP: {result.get('tp_price')}\nSL: {result.get('sl_price')}\nQuantity: {result.get('quantity')}\nتوضیح: {result.get('reason') or 'پس از چک 70 ثانیه‌ای پوزیشن باز بود.'}"
    return '❌ ارسال واقعی ناموفق بود\n' + f"دلیل: {result.get('reason') or 'پوزیشن بعد از 70 ثانیه باز نشد.'}"
