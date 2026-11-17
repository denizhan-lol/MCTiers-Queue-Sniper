#!/usr/bin/env bash
# Arka planda calisan botun canli ekranini gosterir. Cikmak: Ctrl+C (bot durmaz).
cd "$(dirname "$(readlink -f "$0")")" || exit 1
echo "[i] Canli ekran - cikmak icin Ctrl+C (bot calismaya devam eder)"
echo
exec tail -n 50 -f bot.log
