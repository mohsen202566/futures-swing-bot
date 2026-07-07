from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import config
from indicators import Snapshot, snapshot
from okx_data import Candle
from utils import clamp, okx_swap_symbol

Direction = Literal["LONG", "SHORT"]


@dataclass(frozen=True)
class SignalPlan:
    symbol: str
    okx_symbol: str
    toobit_symbol: str
    direction: Direction
    score: float
    strength: str
    entry_price: float
    tp_price: float
    sl_price: float
    risk_reward: float
    sl_pct: float
    tp_pct: float
    estimated_profit_usdt: float
    estimated_loss_usdt: float
    estimated_net_profit_usdt: float
    round_trip_fee_usdt: float
    reasons: tuple[str, ...] = field(default_factory=tuple)

    def to_legacy_dict(self) -> dict[str, object]:
        return {
            "coin": self.symbol,
            "symbol": self.symbol,
            "okx_symbol": self.okx_symbol,
            "toobit_symbol": self.toobit_symbol,
            "direction": self.direction,
            "side": "BUY" if self.direction == "LONG" else "SELL",
            "score": self.score,
            "confidence": self.score,
            "entry": self.entry_price,
            "entry_price": self.entry_price,
            "tp": self.tp_price,
            "tp_price": self.tp_price,
            "sl": self.sl_price,
            "sl_price": self.sl_price,
            "risk_reward": self.risk_reward,
            "tp_percent": self.tp_pct,
            "sl_percent": self.sl_pct,
            "estimated_profit_usdt": self.estimated_profit_usdt,
            "estimated_loss_usdt": self.estimated_loss_usdt,
            "estimated_net_profit_usdt": self.estimated_net_profit_usdt,
            "round_trip_fee_usdt": self.round_trip_fee_usdt,
            "strength": self.strength,
            "reasons": list(self.reasons),
        }


@dataclass(frozen=True)
class DirectionScore:
    direction: Direction | None
    score: float
    reasons: tuple[str, ...]


class Simple4HStrategy:
    """4H trend-pullback re-entry strategy.

    قوانین اصلی نسخه جدید:
    - 4H تایم‌فریم اصلی تحلیل، سیگنال، SL و TP است.
    - 1D فقط فیلتر فشار کلی است: اگر خلاف 4H باشد معامله رد می‌شود، اگر خنثی باشد امتیاز کمتر می‌گیرد.
    - 1H فقط تریگر ورود دقیق‌تر است، نه منبع استاپ و نه روند اصلی.
    - SL از ساختار 4H با بافر ATR ساخته می‌شود.
    - RR نسخه اول ثابت 1.5 است؛ امتیاز قوی فقط برچسب قدرت می‌دهد.
    - رنج، ورود دیر، خلاف روند، DCA، martingale، trailing و AI نداریم.
    """

    def __init__(self) -> None:
        self.min_score = float(config.SIGNAL_SCORE_THRESHOLD)
        self.strong_score = float(config.STRONG_SCORE_THRESHOLD)
        self.last_reject_symbol = ""
        self.last_reject_reason = ""

    def _reject(self, symbol: str, reason: str) -> None:
        self.last_reject_symbol = str(symbol or "").upper()
        self.last_reject_reason = str(reason or "بدون دلیل مشخص")
        return None

    def analyze(
        self,
        symbol: str,
        candles_4h: list[Candle],
        candles_1h: list[Candle],
        candles_1d: list[Candle] | None = None,
        *,
        margin_usdt: float,
        leverage: int,
        toobit_symbol: str | None = None,
        round_trip_fee_usdt: float = config.ROUND_TRIP_FEE_USDT,
    ) -> SignalPlan | None:
        self.last_reject_symbol = str(symbol or "").upper()
        self.last_reject_reason = ""
        s4h = snapshot(candles_4h, swing_lookback=config.SWING_LOOKBACK_4H, slope_lookback=config.EMA_SLOPE_LOOKBACK)
        s1h = snapshot(candles_1h, swing_lookback=config.SWING_LOOKBACK_1H, slope_lookback=config.EMA_SLOPE_LOOKBACK)
        s1d = None
        if candles_1d:
            s1d = snapshot(candles_1d, swing_lookback=config.SWING_LOOKBACK_1D, slope_lookback=config.EMA_SLOPE_LOOKBACK)

        d4 = self._direction_4h(s4h)
        if d4.direction is None:
            return self._reject(symbol, "رد شد: روند 4H واضح نیست")
        direction: Direction = d4.direction

        d1d = self._direction_1d(s1d) if s1d is not None else DirectionScore(None, 0.0, tuple())
        if d1d.direction is not None and d1d.direction != direction:
            return self._reject(symbol, f"رد شد: 1D خلاف 4H است | 1D={d1d.direction} | 4H={direction}")

        reject_reason = self._hard_reject_reason(direction, s4h, s1h, candles_4h, candles_1h)
        if reject_reason:
            return self._reject(symbol, f"رد شد: {reject_reason}")

        entry = s1h.close  # ورود با قیمت آخرین کندل 1H؛ ساختار/استاپ همچنان 4H است.
        sl = self._make_sl_4h(direction, s4h, entry)
        if sl <= 0 or sl == entry:
            return self._reject(symbol, "رد شد: استاپ 4H نامعتبر")

        risk = entry - sl if direction == "LONG" else sl - entry
        if risk <= 0 or s4h.atr <= 0 or entry <= 0:
            return self._reject(symbol, "رد شد: ریسک، ATR یا Entry نامعتبر")

        risk_atr = risk / s4h.atr
        if risk_atr < float(config.MIN_4H_RISK_ATR):
            return self._reject(symbol, f"رد شد: استاپ 4H خیلی نزدیک است | risk={risk_atr:.2f} ATR")
        if risk_atr > float(config.MAX_4H_RISK_ATR):
            return self._reject(symbol, f"رد شد: استاپ 4H خیلی بزرگ است | risk={risk_atr:.2f} ATR")

        sl_pct = risk / entry
        if sl_pct < float(config.MIN_4H_SL_PCT):
            return self._reject(symbol, f"رد شد: فاصله SL خیلی کم است | SL={sl_pct * 100:.2f}%")
        if sl_pct > float(config.MAX_4H_SL_PCT):
            return self._reject(symbol, f"رد شد: فاصله SL خیلی زیاد است | SL={sl_pct * 100:.2f}%")

        score, reasons = self._score(direction, s4h, s1h, d1d, candles_4h, candles_1h, risk_atr)
        if score < self.min_score:
            return self._reject(symbol, f"رد شد: امتیاز پایین است | score={score:.1f}/{self.min_score:.0f}")

        rr = float(config.RR_NORMAL)  # نسخه اول: ثابت 1.5 برای کنترل وین‌ریت و خروج واقع‌بینانه.
        strength = "قوی" if score >= self.strong_score else "معمولی"
        tp = entry + risk * rr if direction == "LONG" else entry - risk * rr
        tp_pct = abs(tp - entry) / entry

        notional = max(0.0, float(margin_usdt)) * max(1, int(leverage))
        gross_profit = notional * tp_pct
        gross_loss = notional * sl_pct
        net_profit = gross_profit - float(round_trip_fee_usdt)

        final_reasons = list(reasons)
        final_reasons.append(f"SL 4H: پشت ساختار 4H با بافر ATR | risk={risk_atr:.2f} ATR")
        final_reasons.append(f"TP: {rr:g}R ثابت بر اساس استاپ 4H")

        return SignalPlan(
            symbol=symbol.upper(),
            okx_symbol=okx_swap_symbol(symbol),
            toobit_symbol=(toobit_symbol or symbol).upper(),
            direction=direction,
            score=round(score, 2),
            strength=strength,
            entry_price=float(entry),
            tp_price=float(tp),
            sl_price=float(sl),
            risk_reward=float(rr),
            sl_pct=float(sl_pct),
            tp_pct=float(tp_pct),
            estimated_profit_usdt=float(gross_profit),
            estimated_loss_usdt=float(gross_loss),
            estimated_net_profit_usdt=float(net_profit),
            round_trip_fee_usdt=float(round_trip_fee_usdt),
            reasons=tuple(final_reasons),
        )

    def _direction_1d(self, s: Snapshot | None) -> DirectionScore:
        if s is None:
            return DirectionScore(None, 0.0, tuple())
        reasons: list[str] = []
        if s.close > s.ema200 and s.ema50 >= s.ema200 and s.ema50 >= s.ema50_lookback:
            reasons.append("1D فشار کلی صعودی")
            return DirectionScore("LONG", 10.0, tuple(reasons))
        if s.close < s.ema200 and s.ema50 <= s.ema200 and s.ema50 <= s.ema50_lookback:
            reasons.append("1D فشار کلی نزولی")
            return DirectionScore("SHORT", 10.0, tuple(reasons))
        reasons.append("1D خنثی است؛ فقط 4H تصمیم‌گیر اصلی است")
        return DirectionScore(None, 4.0, tuple(reasons))

    def _direction_4h(self, s: Snapshot) -> DirectionScore:
        reasons: list[str] = []
        if (
            s.close > s.ema200
            and s.ema50 > s.ema200
            and s.ema50 > s.ema50_lookback
            and s.plus_di > s.minus_di
        ):
            reasons.append("4H روند صعودی: قیمت/EMA50 بالای EMA200 و DMI همسو")
            return DirectionScore("LONG", 25.0, tuple(reasons))
        if (
            s.close < s.ema200
            and s.ema50 < s.ema200
            and s.ema50 < s.ema50_lookback
            and s.minus_di > s.plus_di
        ):
            reasons.append("4H روند نزولی: قیمت/EMA50 زیر EMA200 و DMI همسو")
            return DirectionScore("SHORT", 25.0, tuple(reasons))
        return DirectionScore(None, 0.0, tuple(reasons))

    def _hard_reject_reason(
        self,
        direction: Direction,
        s4h: Snapshot,
        s1h: Snapshot,
        candles_4h: list[Candle],
        candles_1h: list[Candle],
    ) -> str | None:
        if s4h.adx < float(config.MIN_TREND_ADX):
            return "رنج: ADX 4H پایین"
        if s4h.atr <= 0:
            return "ATR 4H نامعتبر"
        if abs(s4h.ema50 - s4h.ema50_lookback) < float(config.FLAT_EMA_ATR_MULT) * s4h.atr:
            return "رنج: EMA50 در 4H صاف است"
        if min(s4h.ema50, s4h.ema200) <= s4h.close <= max(s4h.ema50, s4h.ema200):
            return "رنج/میانه: قیمت 4H بین EMA50 و EMA200 است"
        if self._is_late_4h(direction, s4h, candles_4h):
            return "ورود دیر: قیمت 4H بیش از حد از EMA20/EMA50 دور است"
        if not self._has_4h_pullback(direction, s4h, candles_4h):
            return "بدون پولبک معتبر 4H"
        if not self._has_1h_trigger(direction, s1h, candles_1h):
            return "بدون تریگر معتبر 1H"
        return None

    def _score(
        self,
        direction: Direction,
        s4h: Snapshot,
        s1h: Snapshot,
        d1d: DirectionScore,
        candles_4h: list[Candle],
        candles_1h: list[Candle],
        risk_atr: float,
    ) -> tuple[float, list[str]]:
        score = 0.0
        reasons: list[str] = []

        # 10: 1D pressure filter.
        if d1d.direction == direction:
            score += 10
            reasons.extend(d1d.reasons or ("10 امتیاز: 1D با جهت 4H همسو است",))
        elif d1d.direction is None:
            score += 4
            reasons.extend(d1d.reasons or ("4 امتیاز: 1D خنثی، 4H تصمیم‌گیر اصلی",))

        # 25: 4H trend direction.
        if direction == "LONG" and s4h.close > s4h.ema200 and s4h.ema50 > s4h.ema200 and s4h.plus_di > s4h.minus_di:
            score += 25
            reasons.append("25 امتیاز: 4H روند صعودی واضح")
        elif direction == "SHORT" and s4h.close < s4h.ema200 and s4h.ema50 < s4h.ema200 and s4h.minus_di > s4h.plus_di:
            score += 25
            reasons.append("25 امتیاز: 4H روند نزولی واضح")

        # 15: trend strength.
        if direction == "LONG" and s4h.plus_di > s4h.minus_di:
            if s4h.adx >= float(config.STRONG_TREND_ADX) and s4h.adx >= s4h.prev_adx:
                score += 15
                reasons.append("15 امتیاز: قدرت روند 4H قوی و رو به رشد")
            elif s4h.adx >= float(config.MIN_TREND_ADX):
                score += 11
                reasons.append("11 امتیاز: قدرت روند 4H قابل قبول")
        elif direction == "SHORT" and s4h.minus_di > s4h.plus_di:
            if s4h.adx >= float(config.STRONG_TREND_ADX) and s4h.adx >= s4h.prev_adx:
                score += 15
                reasons.append("15 امتیاز: قدرت روند 4H قوی و رو به رشد")
            elif s4h.adx >= float(config.MIN_TREND_ADX):
                score += 11
                reasons.append("11 امتیاز: قدرت روند 4H قابل قبول")

        # 15: no-range quality.
        ema_slope_atr = abs(s4h.ema50 - s4h.ema50_lookback) / s4h.atr if s4h.atr > 0 else 0.0
        if s4h.adx >= float(config.MIN_TREND_ADX) and ema_slope_atr >= float(config.FLAT_EMA_ATR_MULT):
            score += 15
            reasons.append("15 امتیاز: فیلتر رنج 4H پاس شد")

        # 20: pullback quality on 4H.
        if self._has_4h_pullback(direction, s4h, candles_4h):
            score += 20
            reasons.append("20 امتیاز: پولبک سالم 4H و برگشت به جهت روند")

        # 10: 1H trigger only.
        if self._has_1h_trigger(direction, s1h, candles_1h):
            last = candles_1h[-1]
            body_ratio = abs(last.close - last.open) / max(last.high - last.low, 1e-12)
            if body_ratio >= float(config.MIN_ENTRY_BODY_RATIO):
                score += 10
                reasons.append("10 امتیاز: تریگر 1H با کندل تأیید معتبر")
            else:
                score += 7
                reasons.append("7 امتیاز: تریگر 1H معتبر ولی کندل متوسط")

        # 10: not-late filter.
        if not self._is_late_4h(direction, s4h, candles_4h):
            score += 10
            reasons.append("10 امتیاز: ورود دیر نیست")

        # 5: SL/RR quality.
        if float(config.MIN_4H_RISK_ATR) <= risk_atr <= float(config.MAX_4H_RISK_ATR):
            score += 5
            reasons.append("5 امتیاز: استاپ 4H از نظر ATR منطقی است")

        return clamp(score, 0, 100), reasons

    def _has_4h_pullback(self, direction: Direction, s: Snapshot, candles: list[Candle]) -> bool:
        lookback = max(2, int(config.PULLBACK_LOOKBACK_4H))
        recent = candles[-lookback:]
        buffer = float(config.PULLBACK_ATR_BUFFER) * s.atr
        if direction == "LONG":
            touched_zone = any(c.low <= s.ema20 + buffer for c in recent) or any(c.low <= s.ema50 + buffer for c in recent)
            respected_ema50 = min(c.close for c in recent) >= s.ema50 - buffer
            returned = s.close >= s.ema20 and candles[-1].close >= candles[-1].open
            return touched_zone and respected_ema50 and returned
        touched_zone = any(c.high >= s.ema20 - buffer for c in recent) or any(c.high >= s.ema50 - buffer for c in recent)
        respected_ema50 = max(c.close for c in recent) <= s.ema50 + buffer
        returned = s.close <= s.ema20 and candles[-1].close <= candles[-1].open
        return touched_zone and respected_ema50 and returned

    def _has_1h_trigger(self, direction: Direction, s: Snapshot, candles: list[Candle]) -> bool:
        if len(candles) < 3 or s.atr <= 0:
            return False
        last = candles[-1]
        candle_range = max(last.high - last.low, 1e-12)
        body_ratio = abs(last.close - last.open) / candle_range
        min_body = max(0.30, float(config.MIN_ENTRY_BODY_RATIO) - 0.10)
        if direction == "LONG":
            return (
                last.close > last.open
                and body_ratio >= min_body
                and s.close >= s.ema20
                and s.plus_di >= s.minus_di
                and s.macd_hist >= s.prev_macd_hist
            )
        return (
            last.close < last.open
            and body_ratio >= min_body
            and s.close <= s.ema20
            and s.minus_di >= s.plus_di
            and s.macd_hist <= s.prev_macd_hist
        )

    def _is_late_4h(self, direction: Direction, s: Snapshot, candles: list[Candle]) -> bool:
        if s.atr <= 0:
            return True
        recent = candles[-6:]
        bullish = sum(1 for c in recent if c.close > c.open)
        bearish = sum(1 for c in recent if c.close < c.open)
        if direction == "LONG":
            too_far_20 = (s.close - s.ema20) > float(config.MAX_DISTANCE_EMA20_ATR) * s.atr
            too_far_50 = (s.close - s.ema50) > float(config.MAX_DISTANCE_EMA50_ATR) * s.atr
            too_many = bullish >= 5
            adx_exhaustion = s.adx >= float(config.EXHAUSTION_ADX) and s.adx < s.prev_adx
            return too_far_20 or too_far_50 or too_many or adx_exhaustion
        too_far_20 = (s.ema20 - s.close) > float(config.MAX_DISTANCE_EMA20_ATR) * s.atr
        too_far_50 = (s.ema50 - s.close) > float(config.MAX_DISTANCE_EMA50_ATR) * s.atr
        too_many = bearish >= 5
        adx_exhaustion = s.adx >= float(config.EXHAUSTION_ADX) and s.adx < s.prev_adx
        return too_far_20 or too_far_50 or too_many or adx_exhaustion

    def _make_sl_4h(self, direction: Direction, s: Snapshot, entry: float) -> float:
        buffer = float(config.ATR_SL_BUFFER_MULT) * float(s.atr)
        if direction == "LONG":
            raw = min(float(s.swing_low), float(s.ema50)) - buffer
            if raw >= entry:
                raw = float(s.swing_low) - buffer
            return max(0.0, raw)
        raw = max(float(s.swing_high), float(s.ema50)) + buffer
        if raw <= entry:
            raw = float(s.swing_high) + buffer
        return raw
