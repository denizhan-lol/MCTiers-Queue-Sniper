# 🎯 MCTiers Ultimate QueueSniper

A high-speed Discord client built to monitor queue-based systems, instantly secure a spot via button interaction, and optionally solve captcha challenges using OCR — with an added **sound alert system for instant join feedback**.

---

## 📌 About this repository

Kişisel bir fork / geliştirilmiş sürüm. Orijinal proje:

- **Upstream:** [jayaplayz12/MCTiers-Queue-Sniper](https://github.com/jayaplayz12/MCTiers-Queue-Sniper)

Bu depodaki eklemeler:

- **Çoklu sunucu desteği** — `GUILD_IDS` / `CHANNEL_IDS` ile aynı anda birden fazla
  sunucudaki kuyruk kanalları izlenir
- **Join doğrulama** — butona tıklandıktan sonra kendi kullanıcı ID'si kuyruk
  embed'inde görünene kadar (~12 sn) kontrol edilir; görünmezse "kuyruk dolu
  olabilir" denip tekrar denenir (yanlış "katıldım" bildirimi yok)
- **Dolu kuyruğu atlama** — embed'de `(20/20)` gibi kapasite doluysa tıklanmaz
- **Açılışta geriye dönük tarama** — bot kapalıyken gelen "Join" mesajı kaçmaz
- **5 saniyelik yedek polling** — event kaçarsa mesaj geçmişi taranır
- **Türkçe çıktı + yardımcı script'ler** — `baslat.sh`, `izle.sh`, `durdur.sh`,
  `sifirla.sh`, `hesap.sh`

> ⚠️ Token'lar ve kişisel veriler repoya dahil değildir (`.env`, `bot.log`,
> `bot_state.json`, `server_data_*.json` `.gitignore` içinde).

---

## ⚡ Features

- 🚀 Instant queue joining (auto button click)
- 🎯 Queue position detection from embeds
- 🤖 Captcha solving using OCR
- 🔄 Handles live message edits (real-time queue updates)
- 🔊 Sound alarm when successfully joining
- ⚙️ Fully asynchronous and fast execution

---

## 📦 Requirements

- Python 3.10+ (tested on 3.14)
- Any OS — sound alert uses `winsound` on Windows and the terminal bell elsewhere
- Discord account token *(see warning below)*

### Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

---

## 🟣 Sunucular

Bu depo MCTiers kuyruk sunuculari icin yapilandirildi. Aktif ayar `.env` icinde:

| Sunucu | GUILD_ID | Kanal | CHANNEL_ID |
| --- | --- | --- | --- |
| `[1.21+] Minecraft Sword PvP Community` | `1317975081976332338` | `#waitlist-eu` | `1317975085470187621` |
| `[1.21+] Minecraft Mace PvP Community` **(aktif)** | `1187058381849112606` | `#waitlist-eu` | `1306852692152422491` |
| `[1.21+] Minecraft SMP PvP Community` **(aktif)** | `1224245679749206050` | `#waitlist-eu` | `1224245683129815060` |

Kuyruk botu hepsinde ayni: `MCTIERS` — `1124128173609713734`.

Sunucu degistirmek icin `.env` icindeki `GUILD_ID` ve `CHANNEL_ID` degerlerini
yukaridaki tablodan kopyala; `BOT_ID` ayni kaliyor. Kanal ID'lerini elle bulmak
zorunda degilsin: bot, sunucudaki `waitlist` / `queue` / `tester-needed` isimli
**erisimin olan** kanallari otomatik bulur.

### Sunucu verilerini cekme

```bash
.venv/bin/python main.py --scan
.venv/bin/python main.py --scan --guild 1187058381849112606   # baska sunucu
```

Ayni anda birden fazla sunucu izlemek icin `.env`:

```env
GUILD_IDS=1224245679749206050,1317975081976332338
CHANNEL_IDS=1224245683129815060,1317975085470187621
```

Bot, listelenen tum sunucularda `waitlist` / `queue` / `tester-needed`
kanallarini izler; ayni anda tek kuyruga katilir (ilk acilan).

- Sunucu adi, uye sayisi, rol sayisi, tum kategori/kanal listesi cikar
- Kuyruk kanallarini ve kuyruk botunun ID'sini tespit eder
- Sonucu `server_data_<GUILD_ID>.json` dosyasina yazar (tum kanal + rol verisi)
- Calisan botun durumu `bot_state.json` dosyasinda tutulur

Not: `waitlist-na`, `as-au-waitlist` gibi kanallar hesabinin rolune kapaliysa
`403` doner ve otomatik olarak atlanir.

### Calistirma

Klasik menü ekraniyla (ön planda, `r` + Enter ile sifirlama):

```bash
./baslat.sh
```

Arka planda calistirip canli ekrani izlemek:

```bash
setsid nohup .venv/bin/python -u main.py > bot.log 2>&1 < /dev/null &
./izle.sh          # canli ekran (Ctrl+C botu durdurmaz)
./sifirla.sh       # join durumunu sifirla
./durdur.sh        # botu durdur
```

Kuyruk bitince tekrar katilmak icin konsola `r` yazip Enter'a bas
(veya arka plan modunda `./sifirla.sh`).

---

### Hesaplar

Token'lar Vesktop/Discord'un `Local Storage` verisinden okunur; her hesap icin
ayri `.env.<hesap>` dosyasi tutulur (chmod 600, git'e girmez):

```bash
./hesap.sh                 # mevcut hesaplari ve aktif olani listele
./hesap.sh mermerbaba      # mermerbaba hesabina gec
./hesap.sh ihtiyarmermer   # ihtiyarmermer hesabina gec
```

Not: bazi kuyruk kanallari (or. `#waitlist-eu`) **bolge rolu** ister
(`Waitlist [EU]`). Hesapta bu rol yoksa bot kanali goremez ve uyari basar;
rol Discord arayuzunden alinmali (bot kendine rol veremez).

---

## ⚙️ Setup

### 1. Clone the Repository

```git clone https://github.com/jayaplayz12/MCTiers-Queue-Sniper.git```  
```cd MCTiers-Queue-Sniper``` 

---

### 2. Create `.env`

Create a file named `.env` in the project folder:

DISCORD_TOKEN=your_token_here
GUILD_ID=your_server_id
CHANNEL_ID=target_channel_id
BOT_ID=target_bot_id

---

### 3. Run the Bot

```bash
python main.py
```

To join again after a queue ends, type `r` + Enter in the console to reset the join state.

---

## 🔑 Environment Variables Explained

### DISCORD_TOKEN
- Your Discord account token used for login  
- Gives full access to your account session  
- ⚠️ Never share it with anyone  
- ⚠️ This is **not** your browser cookie header. Values like `__dcfduid`, `__sdcfduid`, `cf_clearance` are Cloudflare/session cookies and will not work.  
- The token is the value stored under `Local Storage → https://discord.com → token` in your browser's DevTools.  

---

### GUILD_ID
- The Discord server ID where the system runs  
- The bot only works inside this server  

👉 “Which server should I monitor?”

---

### CHANNEL_ID
- The specific channel ID where queue messages appear  
- All automation is restricted to this channel  

👉 “Where should the bot watch messages?”

---

### BOT_ID
- The ID of the bot that controls the queue system  
- This bot:
  - Sends queue updates  
  - Shows tester availability  
  - Displays Join buttons  

👉 The script ignores all other users and only reacts to this bot  

👉 “Which bot should I listen to?”

---

## 🧠 How It Works

1. Logs into Discord using your token  
2. Watches a specific channel for messages from the target bot  
3. Detects and clicks the **Join** button instantly  
4. Plays a **ringing sound alert** on successful join  
5. Fetches updated message and extracts queue position  
6. If captcha appears:
   - Downloads image
   - Uses OCR to solve it
   - Sends solution automatically  

---

## 🤖 Captcha System

Some queue systems use captcha images to prevent automation.

This bot handles them automatically:

- Detects captcha image attachments in messages  
- Downloads the image instantly  
- Uses OCR (Optical Character Recognition) to read the text  
- Sends the detected solution back into the chat  
- Continues the queue process automatically  

If OCR succeeds → captcha is solved instantly  
If OCR fails → it waits for the next attempt  

---

## 🔊 Sound Feature

When a successful join happens:
- A high-pitched alert sound is played
- Helps you instantly notice successful queue entry

(On Windows it beeps through `winsound`; elsewhere it rings the terminal bell.)

---

## 📸 Example Output

════════════════════════════════════════  
        MCTIERS AUTO-JOINER ACTIVE      
════════════════════════════════════════  
User:         ExampleUser  
Server:       Example Server  
Channel:      queue-channel  
════════════════════════════════════════  
[-] STATUS: NO TESTER AVAILABLE  
════════════════════════════════════════  

[!] JOIN SUCCESS - ALARM RINGING  

⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐  
Tester Name:    QueueBot  
Timestamp:      14:32:10  
My Queue Pos:   2  
⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐  

---

## 💸 Free & Open

Most tools like this are paid or locked behind subscriptions.  
This project is completely free.

If you want to support development:

- LTC: `ltc1qdfd50nwfs2h2u8l2cama668xf705nfvxty8je4`  
- BTC: `bc1qzjauvt0fytmf9asgsdxgt7z7clhtv8mvzltg0l`  
- ETH: `0x404169F9dF7FC7117C6d76Af08f5390c4B3cCd33`  
- SOL: `62fvBjbwegn397KQJYphBfVjqkZrWbbyyAjzor8tF4oi`  
- USDT (ERC20): `0x404169F9dF7FC7117C6d76Af08f5390c4B3cCd33`  

Donations are optional but appreciated ❤️

---

## ⚠️ Disclaimer

This project is for educational purposes only.

- Self-bots violate Discord Terms of Service  
- Automation may breach platform rules  
- Use can result in account restriction or banning  

Use at your own risk.

---

## 🛠️ Customization

- Change beep sound frequency in `play_ring()`  
- Adjust OCR timing delay  
- Modify queue detection regex  
- Extend for other queue systems  

---

## 🤝 Contributing

Pull requests and improvements are welcome.

---

## ⭐ Support

If you like this project, consider starring the repository ⭐
