#!/usr/bin/env bash
# Hesap degistirir: ./hesap.sh mermerbaba | ./hesap.sh ihtiyarmermer | ./hesap.sh
# Argumansiz calistirilirsa mevcut hesaplari listeler.
cd "$(dirname "$(readlink -f "$0")")" || exit 1

if [ -z "$1" ]; then
  echo "Mevcut hesaplar:"
  for f in .env.*; do
    case "$f" in
      .env.example) continue ;;
    esac
    echo "  - ${f#.env.}"
  done
  echo
  echo "Aktif: $(grep -m1 '^# hesap:' .env 2>/dev/null | sed 's/^# hesap: //')"
  exit 0
fi

name="$1"
src=".env.$name"
if [ ! -f "$src" ]; then
  echo "[X] '$name' bulunamadi. Mevcutlar:"
  ls .env.* 2>/dev/null | grep -v '.env.example' | sed 's/^/  - /; s/\.env\.//'
  exit 1
fi

if [ -f bot.pid ] && kill -0 "$(cat bot.pid)" 2>/dev/null; then
  echo "[!] Bot calisiyor (PID $(cat bot.pid)). Once ./durdur.sh calistir."
  exit 1
fi

cp "$src" .env
chmod 600 .env
echo "[i] Aktif hesap: $name"
