#!/usr/bin/env bash
# Botu durdurur.
cd "$(dirname "$(readlink -f "$0")")" || exit 1
pid=$(cat bot.pid 2>/dev/null)
if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
  kill "$pid"
  echo "[i] Bot durduruldu (PID $pid)."
else
  echo "[i] Calisan bot yok."
fi
