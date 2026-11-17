#!/usr/bin/env bash
# Join durumunu sifirlar (konsolda 'r' yazmakla ayni).
cd "$(dirname "$(readlink -f "$0")")" || exit 1
pid=$(cat bot.pid 2>/dev/null)
if [ -z "$pid" ] || ! kill -0 "$pid" 2>/dev/null; then
  echo "[X] Calisan bot bulunamadi (bot.pid gecersiz)."
  exit 1
fi
kill -USR1 "$pid" && echo "[i] Sifirlama sinyali gonderildi (PID $pid)."
