#!/usr/bin/env bash
# Botu on planda, klasik menü ekraniyla baslatir ('r' + Enter ile join sifirlanir).
cd "$(dirname "$(readlink -f "$0")")" || exit 1

if [ -f bot.pid ] && kill -0 "$(cat bot.pid)" 2>/dev/null; then
  echo "[i] Arka plandaki bot durduruluyor (PID $(cat bot.pid))..."
  kill "$(cat bot.pid)"
  sleep 2
fi

echo $$ > bot.pid
exec .venv/bin/python -u main.py
