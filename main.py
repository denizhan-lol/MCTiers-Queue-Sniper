"""
MCTiers Ultimate QueueSniper - Mace surumu
------------------------------------------
Discord sunucusundaki kuyruk (waitlist / tester-needed) kanallarini izler,
"Join" butonu gorundugu an katilir, captcha'lari OCR ile cozer.

Kullanim:
    .venv/bin/python main.py            # botu baslat
    .venv/bin/python main.py --scan     # sunucu verilerini cek ve raporla
    .venv/bin/python main.py --scan --guild 1187058381849112606
"""

import argparse
import asyncio
import json
import os
import re
import signal
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import discord
import ddddocr
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
STATE_PATH = BASE_DIR / "bot_state.json"


def report_path(guild_id):
    return BASE_DIR / f"server_data_{guild_id}.json"

API = "https://discord.com/api/v10"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/158.0.0.0 Safari/537.36"
)

# Mace sunucusunda kuyruk kanali gibi gorunen isimler (kucuk harfle karsilastirilir)
DEFAULT_KEYWORDS = ("waitlist", "queue", "tester-needed", "tester_needed", "tester needed")

load_dotenv(ENV_PATH)


# --------------------------------------------------------------------------- #
#  Yapilandirma
# --------------------------------------------------------------------------- #
def _env(name, default=None):
    value = os.getenv(name)
    return default if value is None or value.strip() == "" else value.strip()


def _ids(raw):
    if not raw:
        return []
    return [int(p) for p in re.findall(r"\d{15,25}", raw)]


class Config:
    def __init__(self):
        token = _env("DISCORD_TOKEN", "")
        if not token or token.startswith("BURAYA") or "__dcfduid" in token or ";" in token or "=" in token:
            raise SystemExit(
                "\n[X] DISCORD_TOKEN gecersiz.\n"
                "    .env dosyasindaki DISCORD_TOKEN alanina Discord HESAP token'ini yaz.\n"
                "    Not: Tarayici cookie'leri (__dcfduid, cf_clearance vb.) token DEGILDIR.\n"
            )

        guilds_raw = _env("GUILD_IDS") or _env("GUILD_ID")
        guild_ids = _ids(guilds_raw)
        if not guild_ids:
            raise SystemExit("\n[X] GUILD_ID / GUILD_IDS eksik ya da sayi degil. .env dosyasini kontrol et.\n")

        channels = _ids(_env("CHANNEL_IDS") or _env("CHANNEL_ID") or "")
        bot_raw = _env("BOT_ID")
        bot_id = int(bot_raw) if bot_raw and bot_raw.isdigit() else None

        keywords = _env("QUEUE_KEYWORDS")
        if keywords:
            self.keywords = tuple(k.strip().lower() for k in keywords.split(",") if k.strip())
        else:
            self.keywords = DEFAULT_KEYWORDS

        self.token = token
        self.guild_ids = guild_ids
        self.guild_id = guild_ids[0]
        self.channel_ids = channels
        self.bot_id = bot_id
        self.poll_interval = float(_env("POLL_INTERVAL", "5"))


# --------------------------------------------------------------------------- #
#  HTTP yardimcilari (sadece --scan icin, gateway acmadan tum veriyi ceker)
# --------------------------------------------------------------------------- #
class HttpApi:
    def __init__(self, token):
        import aiohttp

        self._aiohttp = aiohttp
        self.session = aiohttp.ClientSession(
            headers={
                "Authorization": token,
                "User-Agent": USER_AGENT,
                "Accept": "*/*",
            }
        )

    async def get(self, path):
        import aiohttp

        url = API + path
        for _ in range(3):
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as r:
                if r.status == 429:
                    retry = float(r.headers.get("Retry-After", "1"))
                    await asyncio.sleep(min(retry, 5) + 0.5)
                    continue
                if r.status >= 400:
                    return {"_error": r.status, "_body": (await r.text())[:400]}
                return await r.json()
        return {"_error": 429, "_body": "rate limited"}

    async def close(self):
        await self.session.close()


def _channel_type_name(t):
    return {
        0: "metin",
        2: "ses",
        4: "kategori",
        5: "duyuru",
        13: "stage",
        15: "forum",
    }.get(t, str(t))


async def scan_server(guild_id: int):
    """Sunucudaki tum veriyi cekip ekrana basar ve mace_server_data.json'a yazar."""
    cfg_token = _env("DISCORD_TOKEN", "")
    if not cfg_token:
        raise SystemExit("[X] DISCORD_TOKEN bulunamadi")

    api = HttpApi(cfg_token)
    try:
        me = await api.get("/users/@me")
        if "_error" in me:
            raise SystemExit(f"[X] Token gecersiz ({me['_error']}): {me['_body']}")

        guild = await api.get(f"/guilds/{guild_id}?with_counts=true")
        if "_error" in guild:
            raise SystemExit(f"[X] Sunucu okunamadi ({guild['_error']}): {guild['_body']}")

        print("=" * 62)
        print("  SUNUCU VERILERI")
        print("=" * 62)
        print(f"Hesap        : {me['username']}  (id={me['id']})")
        print(f"Sunucu       : {guild['name']}")
        print(f"Sunucu ID    : {guild['id']}")
        print(f"Uye sayisi   : {guild.get('approximate_member_count')} (aktif: {guild.get('approximate_presence_count')})")
        print(f"Sahip olunan : {len(guild.get('roles', []))} rol")
        print(f"Olusturulma  : {guild.get('id') and datetime.fromtimestamp(((int(guild['id']) >> 22) + 1420070400000) / 1000).strftime('%Y-%m-%d')}")

        channels = await api.get(f"/guilds/{guild_id}/channels")
        if "_error" in channels:
            raise SystemExit(f"[X] Kanallar okunamadi: {channels}")
        roles = guild.get("roles", [])
        by_id = {c["id"]: c for c in channels}

        categories = [c for c in channels if c.get("type") == 4]
        print(f"Kanal sayisi : {len(channels)} (kategori: {len(categories)})")
        print("-" * 62)

        # Kategorilere gore listele
        for cat in sorted(categories, key=lambda c: c.get("position", 0)):
            print(f"\n[{cat['name']}]")
            kids = sorted([c for c in channels if c.get("parent_id") == cat["id"]], key=lambda c: c.get("position", 0))
            for c in kids:
                print(f"   {_channel_type_name(c.get('type')):<8} #{c['name']}  ({c['id']})")
        orphans = [c for c in channels if c.get("type") != 4 and not c.get("parent_id")]
        if orphans:
            print("\n[kategorisiz]")
            for c in orphans:
                print(f"   {_channel_type_name(c.get('type')):<8} #{c['name']}  ({c['id']})")

        # Kuyruk adayi kanallari incele
        keywords = DEFAULT_KEYWORDS
        candidates = [
            c for c in channels
            if c.get("type") in (0, 5) and any(k in c["name"].lower() for k in keywords)
        ]
        print("\n" + "=" * 62)
        print("  KUYRUK KANALLARI")
        print("=" * 62)
        found = []
        for c in candidates:
            cat = by_id.get(c.get("parent_id"), {}).get("name", "-")
            msgs = await api.get(f"/channels/{c['id']}/messages?limit=10")
            if isinstance(msgs, dict):
                print(f"#{c['name']:<28} [{cat}] -> erisim yok ({msgs['_error']})")
                continue
            authors = {}
            join_msgs = []
            for m in msgs:
                a = m["author"]
                authors[a["id"]] = a["username"]
                labels = [
                    ch.get("label") or ""
                    for row in (m.get("components") or [])
                    for ch in row.get("components", [])
                ]
                if any("join" in l.lower() for l in labels):
                    join_msgs.append(m)
            last = msgs[0] if msgs else {}
            print(
                f"#{c['name']:<28} [{cat}] -> OK  son mesaj: "
                f"{last.get('timestamp', '-')[:19]} {last.get('author', {}).get('username', '-')}"
            )
            if authors:
                print(f"    yazarlar: {', '.join(f'{u} ({i})' for i, u in authors.items())}")
            found.append(
                {
                    "id": c["id"],
                    "name": c["name"],
                    "category": cat,
                    "message_count_checked": len(msgs),
                    "authors": authors,
                    "last_message_at": last.get("timestamp"),
                    "join_button_found": bool(join_msgs),
                }
            )

        # Kuyruk botunu tespit et: join butonu olan mesajin sahibi
        bot_id = None
        for item in found:
            if item["join_button_found"]:
                bot_id = next(iter(item["authors"]), None)
                break
        if bot_id is None:
            for item in found:
                for aid, uname in item["authors"].items():
                    if uname.upper() in ("MCTIERS", "MACE"):
                        bot_id = aid
                        break
                if bot_id:
                    break

        print("\n" + "=" * 62)
        print("  TESPIT EDILEN AYARLAR (.env icin)")
        print("=" * 62)
        print(f"GUILD_ID   = {guild_id}")
        print(f"CHANNEL_ID = {found[0]['id'] if found else '<kuyruk kanali bulunamadi>'}")
        print(f"BOT_ID     = {bot_id or '<tespit edilemedi>'}")
        print(f"CHANNEL_IDS= {','.join(str(f['id']) for f in found)}")

        report = {
            "scanned_at": datetime.now(timezone.utc).isoformat(),
            "account": {"id": me["id"], "username": me["username"]},
            "guild": {
                "id": guild["id"],
                "name": guild["name"],
                "member_count": guild.get("approximate_member_count"),
                "presence_count": guild.get("approximate_presence_count"),
                "role_count": len(roles),
                "roles": [{"id": r["id"], "name": r["name"]} for r in roles],
            },
            "channels": [
                {
                    "id": c["id"],
                    "name": c["name"],
                    "type": _channel_type_name(c.get("type")),
                    "parent_id": c.get("parent_id"),
                    "category": by_id.get(c.get("parent_id"), {}).get("name"),
                }
                for c in channels
            ],
            "queue_channels": found,
            "detected_bot_id": bot_id,
        }
        out = report_path(guild_id)
        out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\n[i] Tum veri kaydedildi: {out}")
    finally:
        await api.close()


# --------------------------------------------------------------------------- #
#  Bot
# --------------------------------------------------------------------------- #
class QueueSniper(discord.Client):
    def __init__(self, config: Config, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cfg = config
        self.oc = ddddocr.DdddOcr(show_ad=False)
        self.channels = []            # izlenecek kanallar
        self.bot_id = config.bot_id   # kuyruk botu
        self.joined = {}              # channel_id -> bilgi
        self.last_join_at = 0.0
        self._captcha_lock = asyncio.Lock()
        self._poll_task = None
        try:
            signal.signal(signal.SIGUSR1, self.reset_join)
        except (ValueError, AttributeError):
            pass

    def reset_join(self, *_):
        self.joined.clear()
        print("[i] Join durumu sifirlandi, tekrar katilim denenecek.")

    # -- yardimcilar ------------------------------------------------------- #
    def play_ring(self):
        for _ in range(4):
            try:
                import winsound  # sadece Windows'ta var

                winsound.Beep(2000, 150)
                winsound.Beep(2500, 150)
            except Exception:
                print("\a", end="", flush=True)

    def console_listener(self):
        if not sys.stdin or not sys.stdin.isatty():
            return
        for line in sys.stdin:
            if line.strip().lower() in ("r", "reset"):
                self.reset_join()

    def get_queue_position(self, embeds):
        for embed in embeds:
            desc = embed.description or ""
            match = re.search(rf"(\d+)\.\s*<@!?{self.user.id}>", desc)
            if match:
                return match.group(1)
        return "Position pending..."

    async def resolve_channels(self, guild):
        found = {}
        for cid in self.cfg.channel_ids:
            ch = self.get_channel(cid)
            if ch is None:
                try:
                    ch = await self.fetch_channel(cid)
                except Exception:
                    ch = None
            if ch is not None:
                found[ch.id] = ch

        for ch in guild.channels:
            if getattr(ch, "type", None) not in (discord.ChannelType.text, discord.ChannelType.news):
                continue
            if not any(k in ch.name.lower() for k in self.cfg.keywords):
                continue
            perms = ch.permissions_for(guild.me)
            if not (perms.view_channel and perms.read_message_history):
                continue
            found[ch.id] = ch

        return sorted(found.values(), key=lambda c: c.name)

    async def detect_bot(self, channels):
        if self.bot_id:
            return self.bot_id
        for ch in channels:
            try:
                async for msg in ch.history(limit=10):
                    if msg.author.id == self.user.id:
                        continue
                    labels = [
                        getattr(c, "label", "") or ""
                        for row in (msg.components or [])
                        for c in getattr(row, "children", [])
                    ]
                    if any("join" in l.lower() for l in labels):
                        return msg.author.id
                    if (msg.author.bot or msg.author.name.upper() == "MCTIERS") and msg.embeds:
                        return msg.author.id
            except Exception:
                continue
        return None

    @staticmethod
    def short_guild(name):
        for prefix in ("[1.21+] Minecraft ", "[1.21.11+] Minecraft ", "[1.21+] "):
            if name.startswith(prefix):
                name = name[len(prefix):]
        return name.replace(" PvP Community", "").replace(" Community", "").strip()

    def save_report(self, guilds):
        data = {
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "guilds": [
                {"id": g.id, "name": g.name, "member_count": g.member_count} for g in guilds
            ],
            "watching": [
                {
                    "id": c.id,
                    "name": c.name,
                    "guild": c.guild.name,
                    "category": getattr(c.category, "name", None),
                }
                for c in self.channels
            ],
            "queue_bot_id": self.bot_id,
        }
        try:
            STATE_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            print(f"[X] Rapor yazilamadi: {e}")

    # -- olaylar ------------------------------------------------------------ #
    async def on_ready(self):
        print("\n" + "═" * 40)
        print("        MCTIERS AUTO-JOINER ACTIVE      ")
        print("═" * 40)
        print(f"User:         {self.user.name}")

        guilds = []
        for gid in self.cfg.guild_ids:
            g = self.get_guild(gid)
            if g is None:
                try:
                    g = await self.fetch_guild(gid)
                except Exception as e:
                    print(f"[!] Sunucu atlandi ({gid}): {e}")
                    continue
            guilds.append(g)

        if not guilds:
            print("[X] Hicbir sunucuya erisilemedi. .env icindeki GUILD_IDS'i kontrol et.")
            await self.close()
            return

        found = {}
        for g in guilds:
            for ch in await self.resolve_channels(g):
                found[ch.id] = ch
        self.channels = sorted(found.values(), key=lambda c: (c.guild.name, c.name))
        self.bot_id = await self.detect_bot(self.channels)

        if not self.channels:
            print("[X] Izlenecek kuyruk kanali bulunamadi. .env icindeki CHANNEL_ID'yi kontrol et.")
            await self.close()
            return

        print(f"Server:       {', '.join(self.short_guild(g.name) for g in guilds)}")
        print(
            "Channel:      "
            + ", ".join(f"#{ch.name} ({self.short_guild(ch.guild.name)})" for ch in self.channels)
        )
        print(f"Queue Bot:    {self.bot_id or 'tespit edilemedi'}")
        for ch in self.channels:
            perms = ch.permissions_for(ch.guild.me)
            if not (perms.view_channel and perms.read_message_history):
                print(f"[!] UYARI: #{ch.name} ({self.short_guild(ch.guild.name)}) bu hesaba kapali (bolge rolu eksik olabilir).")
        print("═" * 40)
        print("[-] STATUS: NO TESTER AVAILABLE")
        print("═" * 40)
        print("[i] Tekrar katilim icin konsola 'r' yazip Enter'a bas.\n")

        self.save_report(guilds)

        # Acilista son mesajlari kontrol et (bot kapaliyken gelen Join kacmasin)
        for ch in self.channels:
            await self.scan_recent(ch)

        threading.Thread(target=self.console_listener, daemon=True).start()
        self._poll_task = asyncio.create_task(self.poll_loop())

    async def scan_recent(self, channel, limit=10):
        try:
            async for msg in channel.history(limit=limit):
                if self.bot_id and msg.author.id != self.bot_id:
                    continue
                await self.attempt_join(msg)
                if msg.attachments and not self.joined:
                    asyncio.create_task(self.solve_captcha(msg))
        except Exception as e:
            print(f"[X] #{channel.name} okunamadi: {e}")

    async def poll_loop(self):
        """Gateway edit olayi kacarsa diye hafif yedek tarama."""
        while not self.is_closed():
            try:
                await asyncio.sleep(self.cfg.poll_interval)
                if self.joined:
                    continue
                for ch in self.channels:
                    async for msg in ch.history(limit=2):
                        if self.bot_id and msg.author.id != self.bot_id:
                            continue
                        await self.attempt_join(msg)
            except asyncio.CancelledError:
                return
            except Exception:
                await asyncio.sleep(2)

    async def attempt_join(self, message):
        if self.joined:
            return False
        if not message.components:
            return False

        # Kuyruk doluysa tiklamayi denemeden atla ( "(20/20)" gibi )
        embed_text = "\n".join((e.description or "") for e in (message.embeds or []))
        cap = re.search(r"\((\d+)\s*/\s*(\d+)\)", embed_text)
        if cap and int(cap.group(1)) >= int(cap.group(2)):
            return False

        for row in message.components:
            for child in getattr(row, "children", []):
                label = (getattr(child, "label", "") or "")
                custom = (getattr(child, "custom_id", "") or "")
                if getattr(child, "type", None) != discord.ComponentType.button:
                    continue
                if "join" not in label.lower() and "join" not in custom.lower():
                    continue

                try:
                    # Tiklamadan once isaretle: ayni anda gelen iki mesaja iki kez tiklamayalim
                    self.joined[message.channel.id] = {"message_id": message.id}
                    self.last_join_at = time.time()
                    await child.click()

                    # Kuyruk dolu olabilir: gercekten listeye girdik mi diye dogrula
                    joined_ok = False
                    pos = "Position pending..."
                    updated = message
                    for _ in range(6):
                        await asyncio.sleep(2)
                        try:
                            updated = await message.channel.fetch_message(message.id)
                        except Exception:
                            continue
                        text = "\n".join((e.description or "") for e in updated.embeds)
                        if str(self.user.id) in text:
                            joined_ok = True
                            pos = self.get_queue_position(updated.embeds)
                            break

                    if not joined_ok:
                        self.joined.pop(message.channel.id, None)
                        print(
                            f"[!] Join denemesi basarisiz: #{message.channel.name} "
                            f"({self.short_guild(message.channel.guild.name)}) - kuyruk dolu olabilir."
                        )
                        return False

                    self.play_ring()
                    print("\n[!] JOIN SUCCESS - ALARM RINGING")
                    print(f"    Kanal:      #{message.channel.name} ({self.short_guild(message.channel.guild.name)})")
                    region = getattr(message.channel, "category", None)

                    print("\n" + "*" * 20)
                    print(f"Tester Name:    {updated.author.name}")
                    print(f"Region:         {getattr(region, 'name', message.channel.name)}")
                    print(f"Timestamp:      {time.strftime('%H:%M:%S')}")
                    print(f"My Queue Pos:   {pos}")
                    print("*" * 20 + "\n")
                    return True
                except Exception as e:
                    self.joined.pop(message.channel.id, None)
                    print(f"[X] Click Error: {e}")
        return False

    async def on_message(self, message):
        if message.channel.id not in {c.id for c in self.channels}:
            return
        if self.bot_id and message.author.id != self.bot_id:
            return
        if not self.joined:
            await self.attempt_join(message)
        if message.attachments and not self.joined:
            asyncio.create_task(self.solve_captcha(message))

    async def on_message_edit(self, before, after):
        if after.channel.id not in {c.id for c in self.channels}:
            return
        if self.bot_id and after.author.id != self.bot_id:
            return
        if not self.joined:
            await self.attempt_join(after)

    async def solve_captcha(self, message):
        if self._captcha_lock.locked():
            return
        async with self._captcha_lock:
            try:
                attachment = message.attachments[0]
                if attachment.content_type and not attachment.content_type.startswith("image/"):
                    return
                img = await attachment.read()
                solution = self.oc.classification(img)
                if solution:
                    await asyncio.sleep(0.5)
                    await message.channel.send(solution)
                    print(f"[@] Captcha Solved: {solution}")
            except Exception as e:
                print(f"[X] Captcha Error: {e}")


# --------------------------------------------------------------------------- #
async def main_async(args):
    if args.scan:
        ids = _ids(_env("GUILD_IDS") or _env("GUILD_ID") or "")
        guild_id = args.guild or (ids[0] if ids else 0)
        if not guild_id:
            raise SystemExit("[X] --guild ver ya da .env icinde GUILD_ID tanimla.")
        await scan_server(guild_id)
        return

    cfg = Config()
    client = QueueSniper(cfg)
    try:
        await client.start(cfg.token)
    except discord.LoginFailure:
        print("\n[X] Giris basarisiz: token gecersiz veya suresi dolmus.\n")
    except KeyboardInterrupt:
        print("\n[i] Kapatiliyor...")
    finally:
        if not client.is_closed():
            await client.close()


def main():
    parser = argparse.ArgumentParser(description="MCTiers QueueSniper (Mace)")
    parser.add_argument("--scan", action="store_true", help="Sunucu verilerini cek ve raporla")
    parser.add_argument("--guild", type=int, help="Taranacak sunucu ID'si")
    args = parser.parse_args()

    try:
        asyncio.run(main_async(args))
    except KeyboardInterrupt:
        print("\n[i] Kapatiliyor...")


if __name__ == "__main__":
    main()
