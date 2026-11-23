import asyncio
import json
import os
import random
import sqlite3
import subprocess
import textwrap
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    WebAppInfo,
)

# ---------- 1. WEB KEEP-ALIVE (Render) ----------
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Akirky Kat Bot is running!")

    def log_message(self, *args):
        pass


def run_web():
    port = int(os.getenv("PORT", 10000))
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()


threading.Thread(target=run_web, daemon=True).start()

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable орнотулган эмес!")

MINI_APP_URL = os.getenv("MINI_APP_URL", "").strip()
bot = Bot(token=TOKEN)
dp = Dispatcher()

WORK_DIR = "/tmp/akirky_kat"
os.makedirs(WORK_DIR, exist_ok=True)

conn = sqlite3.connect(os.path.join(WORK_DIR, "akirky_kat.db"), check_same_thread=False)
cur = conn.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS progress (user_id INTEGER PRIMARY KEY, episode INTEGER DEFAULT 0)")
cur.execute("CREATE TABLE IF NOT EXISTS subs (user_id INTEGER PRIMARY KEY, subscribed INTEGER DEFAULT 0)")
conn.commit()

# ---------- 2. СЕРИАЛ МААЛЫМАТ ----------
SERIES_NAME = "💔 АКЫРКЫ КАТ"
MAIN_HERO = "Айдана - 18 жашта, узун кара чачтуу аниме кыз"
HERO2 = "Эмир - 19 жашта, көк көз аниме бала"
SETTING = "Бишкек, күз, жамгырлуу шаар"

EPISODES = [
    {
        "num": 1,
        "title": "1-серия: Акыркы кат",
        "hook": "Ал катты 3 жылдан бери эч кимге көрсөткөн эмес...",
        "script": """Ал катты 3 жылдан бери эч кимге көрсөткөн эмес.
Айдана ошол күнү мектептин эски шкафынан бир кат табат.
Конвертте бир гана сөз жазылган: Эмирге.
Ал ачпай туруп эле жүрөгү токтоп калгандай болот.
Анткени Эмир, 3 жыл мурун жоголуп кеткен.
Ал катты ачат. Биринчи сапты окуйт да, колу титирей баштайт.
Анда мындай деп жазылган: Эгер сен муну окуп жатсаң, демек мен кайтып келдим.
Бирок Айдана терезеге караса, көчөдө эч ким жок.
Уландысы 2-серияда...""",
        "mood": "sad",
    },
    {
        "num": 2,
        "title": "2-серия: Ким жазган?",
        "hook": "Бул катты Эмир жазган эмес...",
        "script": """Айдана катты кайра-кайра окуйт.
Кол жазма Эмирдики эмес. Бул кол жазманы ал тааныйт. Бул анын өзүнүн кол жазмасы.
Айдана 3 жыл мурун өзү өзүнө кат жазганбы? Эмне үчүн ал муну унуткан?
Каттын аягында дагы бир сап бар: Эртең, саат 5те, эски көпүрөгө кел. Жалгыз кел.
Айдана коркот. Бирок барбаса болбойт.
Эртеси ал көпүрөгө барат. Анан ал жерде турган адамды көрүп тоңуп калат.
Ал Эмир эле.
Уландысы 3-серияда...""",
        "mood": "mystery",
    },
    {
        "num": 3,
        "title": "3-серия: Сен тирүү белең?",
        "hook": "Ал өлгөн деп ойлогон адам тирүү болуп чыкты...",
        "script": """Эмир? Сен тирүү белең?
Эмир жылмайып карайт. Бирок бул жылмаюу мурункудай эмес.
Мен сага 3 жыл мурун кат жазгам, дейт ал. Бирок ал кат сага жеткен эмес. Анткени аны бирөө жашырып койгон.
Айдананын көзүнө жаш толуп кетет. Ким? Ким жашырган?
Эмир жооп бербейт. Ал болгону чөнтөгүнөн эски сүрөттү чыгарып берет.
Сүрөттө Айдана менен Эмир эмес, үчүнчү адам турат.
Ал адамды көрүп Айдананын жүрөгү түшүп кетет.
Анткени ал адам анын эң жакын досу эле.
Уландысы 4-серияда...""",
        "mood": "drama",
    },
    {
        "num": 4,
        "title": "4-серия: Эң жакын дос",
        "hook": "Чындыкты жашырган адам - анын эң жакын досу болуп чыкты...",
        "script": """Айдана сүрөттү колуна кармап турат. Сүрөттө Арууке турат. Анын эң жакын досу. Үч жылдан бери жанында жүргөн, ыйлаганында кучактаган адам.
Эмир акырын сүйлөйт: Арууке менин катымды жашырган. Ал сени жоготкум келген эмес дейт, бирок чындык башка.
Айдана ишенбейт. Арууке мындай кылмак эмес. Ал мени эч качан сатпайт, дейт.
Бирок ошол замат телефону титирейт. Аруукеден билдирүү келет: Айдана, кечир. Мен сага баарын айтышым керек. Эртең жолугалы.
Айдананын колу титирейт. Ал кимге ишенээрин билбейт.
Уландысы 5-серияда...""",
        "mood": "drama",
    },
    {
        "num": 5,
        "title": "5-серия: Арууке эмне дейт?",
        "hook": "Арууке чындыкты айтканда, баары өзгөрөт...",
        "script": """Эртеси Айдана Арууке менен жолугат. Кафеде эч ким жок. Жамгыр терезеге урулуп жатат.
Арууке көзүнө карай албайт. Мен сени коргогум келген, дейт ал.
Эмир кетээрде мага айткан: Мен кетпесем, Айданага жаман болот.
Айдана таң калат. Эмне? Эмне болмок?
Арууке ыйлап жиберет. Анткени Эмирдин үй-бүлөсү аларды бөлгүсү келген. Алар Айдананы коркутушкан.
Ошон үчүн Эмир кеткен. Ошон үчүн катты жашырганмын.
Айдана ордунан турат. Анда эмне үчүн азыр кайтып келди? деп сурайт.
Арууке шыбырап айтат: Анткени ал дагы кетип жатат. Бул жолу биротоло.
Уландысы 6-серияда...""",
        "mood": "sad",
    },
    {
        "num": 6,
        "title": "6-серия: Экинчи барак",
        "hook": "Каттын экинчи барагин эч ким окуган эмес...",
        "script": """Айдана үйгө чуркап барып катты кайра ачат. Ал биринчи баракты гана окуган экен. Конверттин ичинде дагы бир барак бар.
Экинчи баракта бир гана сүйлөм жазылган: Эгер мен кетсем, мени издебе. Мени унут.
Айдана ыйлап жиберет. Ал үч жыл бою унуткан эмес. Унуткусу да келген эмес.
Ошол замат эшик кагылат. Айдана эшикти ачса, Эмир турат. Колунда гүл эмес, чемодан бар.
Мен эртең кетем, дейт Эмир. Бирок кетээрден мурун сага бир нерсени көрсөткүм келет.
Ал телефонун чыгарып, бир видеону көрсөтөт. Видеодо Айдана өзү турат. Үч жыл мурунку Айдана.
Ал видеодо эмне дегенин укканда, Айдананын жүрөгү токтоп калат.
Уландысы 7-серияда...""",
        "mood": "drama",
    },
    {
        "num": 7,
        "title": "7-серия: Унутулган видео",
        "hook": "Ал видео үч жыл мурун тартылган, бирок ал аны эстебейт...",
        "script": """Видеодо Айдана күлүп турат. Ал айтат: Эмир, эгер сен муну көрүп жатсаң, демек мен баарын унуттум.
Айдана таң калат. Мен качан муну айткам? Эмне үчүн унуттум?
Эмир айтат: Сен аварияга кабылгансың. Ошол күнү. Мен кеткен күнү.
Айдананын башы ооруй баштайт. Эскерүүлөр кайтып келе баштайт. Жамгыр. Машина. Эмирдин кыйкырганы.
Ал эстейт. Ал күнү Эмир аны сактап калган. Өзү кетүүнүн ордуна, аны ооруканага алып барган.
Мен сени сактап калдым, бирок сени жоготуп алдым, дейт Эмир.
Айдана ыйлап, аны кучактап алат. Кечир мени, дейт. Мен эстедим. Баарын эстедим.
Бирок ошол учурда Эмирдин телефону чалат. Ал телефонду карап, жүзү өзгөрүп кетет.
Уландысы 8-серияда...""",
        "mood": "sad",
    },
    {
        "num": 8,
        "title": "8-серия: Акыркы чалуу",
        "hook": "Бул чалуу баарын чечет...",
        "script": """Эмир телефонду алат. Анын апасы чалып жатат. Үнү катуу чыгат: Эмир, кайдасың? Учак бир сааттан кийин учат.
Айдана муну угат. Учак? Кайда учасың?
Эмир жооп бербейт. Ал терезеге карайт. Жамгыр токтогон эмес.
Мен сени үч жыл күттүм, дейт Айдана. Эми кайра кетип жатасыңбы?
Эмир бурулуп карайт. Көзүндө жаш бар. Эгер калсам, сени дагы жоготом. Эгер кетсем, сени түбөлүк жоготом.
Айдана анын колун кармайт. Кал. Бул жолу чогуу чечебиз.
Эмир жылмаят. Бирок ошол жылмаюу коштошуу жылмаюусуна окшош.
Ал чөнтөгүнөн акыркы нерсени чыгарат. Бул кичинекей куту. Кутунун ичинде...
Уландысы 9-серияда...""",
        "mood": "drama",
    },
    {
        "num": 9,
        "title": "9-серия: Кичинекей куту",
        "hook": "Ал кутунун ичинде үч жылдык сыр жатат...",
        "script": """Эмир кутуну ачат. Ичинде шакек жок. Ичинде эски билет жатат. Үч жыл мурунку билет.
Бул биздин биринчи жолугушуубуздун билети, дейт Эмир. Мен аны үч жыл бою сактап жүрдүм.
Айдана билетти кармайт. Билеттин артында бир нерсе жазылган: Кайда болсоң да, мен сени табам.
Айдана ыйлап жиберет. Анда кал да. Мени кайра таппа. Жанымда кал.
Эмир аны кучактап алат. Бирок анын телефону кайра чалат. Бул жолу Арууке.
Арууке ыйлап айтат: Эмир, бол. Атаң келип жатат. Ал Айдананын үйүнө баратат.
Эшик кайра кагылат. Бул жолу катуу. Айдана менен Эмир бири-бирин карашат.
Эшиктин артында ким турат?
Уландысы 10-серияда...""",
        "mood": "mystery",
    },
    {
        "num": 10,
        "title": "10-серия: Эшиктин артында ким?",
        "hook": "Бул серияда баары чечилет деп ойлогонсуңбу? Жок...",
        "script": """Эшик ачылат. Арууке турат. Ал дем алып жетишпей турат. Көчөдө жамгыр катуу жаап жатат.
Ал кыйкырат: Качкыла! Атасы келип жатат. Ал силерди кайра бөлгүсү келет.
Айдана менен Эмир бири-бирин карашат. Үч жыл мурун да дал ушундай болгон.
Бирок бул жолу Айдана качпайт. Ал алдыга чыгат. Жетишет, дейт ал. Үч жыл качтык. Эми качпайбыз.
Эмир анын колун кармайт. Экөө чогуу эшикти көздөй басышат.
Камера алардын артынан тартат. Жамгыр. Эки кол. Бир кат.
Ал кат азыр да столдун үстүндө жатат. Конверттин үстүндө: Эмирге.
Бирок бул жолу кат жабылган эмес. Ал ачык турат.
Анткени окуя эми гана башталып жатат.
1-сезон бүттү. 2-сезондо эмне болот? Жазылып кой, кийинки сезонду өткөрүп жибербе.""",
        "mood": "drama",
    },
]


def get_episode(n: int) -> dict:
    if 1 <= n <= len(EPISODES):
        return EPISODES[n - 1]
    return {
        "num": n,
        "title": f"{n}-серия: Акыркы кат",
        "hook": "Бул сыр дагы тереңдеп баратат...",
        "script": (
            f"Акыркы кат сериалы, {n}-серия. Айдана чындыкка дагы бир кадам жакындады. "
            f"Бирок ар бир жооп жаңы суроо жаратат. Уландысы {n + 1}-серияда..."
        ),
        "mood": "sad",
    }


# ---------- 3. КЛАВИАТУРАЛАР ----------
def main_kb() -> ReplyKeyboardMarkup:
    row2 = [KeyboardButton(text="📜 1-сериядан баштоо")]
    if MINI_APP_URL.startswith("https://") and "t.me/" not in MINI_APP_URL:
        row2.append(KeyboardButton(text="🎮 Mini App'та ойноо", web_app=WebAppInfo(url=MINI_APP_URL)))
    else:
        row2.append(KeyboardButton(text="🎮 Mini App"))

    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="▶️ Кийинки серия")],
            row2,
            [KeyboardButton(text="ℹ️ Сериал жөнүндө"), KeyboardButton(text="❤️ Жазылуу")],
        ],
        resize_keyboard=True,
    )


# ---------- 4. ҮН + УЗАКТЫК ----------
async def make_voice(text: str, out_path: str, voice: str = "ky-KG-AigulNeural") -> bool:
    try:
        import edge_tts

        comm = edge_tts.Communicate(text, voice)
        await comm.save(out_path)
        return os.path.exists(out_path) and os.path.getsize(out_path) > 0
    except Exception as e:
        print("VOICE ERROR:", e)
        return False


def get_audio_duration(audio_path: str, fallback: float = 45.0) -> float:
    try:
        res = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", audio_path],
            capture_output=True,
            text=True,
            check=True,
        )
        data = json.loads(res.stdout)
        dur = float(data["format"]["duration"])
        return dur if dur > 1.0 else fallback
    except Exception:
        return fallback


# ---------- 5. СУБТИТР (SRT) ----------
def make_subtitles(script_text: str, duration: float = 45.0, out_srt: str = "/tmp/akirky_kat/subs.srt") -> str:
    lines = [l.strip() for l in script_text.splitlines() if l.strip() and "Уландысы" not in l]
    blocks = [" ".join(lines[i : i + 2]) for i in range(0, len(lines), 2)] or [script_text[:80]]
    per = duration / max(len(blocks), 1)

    def fmt(t: float) -> str:
        t = max(0.0, t)
        h = int(t // 3600)
        m = int((t % 3600) // 60)
        s = int(t % 60)
        ms = int((t - int(t)) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    srt_parts = []
    for i, b in enumerate(blocks):
        wrapped = "\n".join(textwrap.wrap(b.upper(), width=26))
        srt_parts.append(f"{i + 1}\n{fmt(i * per)} --> {fmt((i + 1) * per)}\n{wrapped}\n")

    with open(out_srt, "w", encoding="utf-8") as f:
        f.write("\n".join(srt_parts))
    return out_srt


# ---------- 6. АНИМЕ СҮРӨТ ----------
def load_font(size: int):
    from PIL import ImageFont

    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def make_anime_image(ep: dict, out_path: str) -> bool:
    try:
        from PIL import Image, ImageDraw

        colors = {"sad": (30, 30, 70), "mystery": (20, 40, 50), "drama": (70, 20, 40)}
        bg = colors.get(ep.get("mood", "sad"), (30, 30, 70))
        img = Image.new("RGB", (1080, 1920), bg)
        d = ImageDraw.Draw(img)

        for _ in range(300):
            x = random.randint(0, 1080)
            y = random.randint(0, 1920)
            d.line([(x, y), (x - 10, y + 30)], fill=(150, 150, 200), width=2)

        f_title = load_font(56)
        f_sub = load_font(44)
        f_hook = load_font(42)
        f_foot = load_font(34)

        d.text((60, 760), SERIES_NAME, fill=(255, 255, 255), font=f_title)
        d.text((60, 840), ep["title"], fill=(255, 220, 0), font=f_sub)

        y = 960
        for line in textwrap.wrap(ep["hook"], width=28):
            d.text((60, y), line, fill=(255, 255, 255), font=f_hook)
            y += 58

        d.text((60, 1780), "АКЫРКЫ КАТ • Shorts", fill=(200, 200, 200), font=f_foot)
        img.save(out_path)
        return os.path.exists(out_path)
    except Exception as e:
        print("IMAGE ERROR:", e)
        return False


# ---------- 7. МУЗЫКА + МОНТАЖ ----------
def make_video(image_path: str, audio_path: str, srt_path: str, out_path: str, music_path: str | None = None) -> bool:
    style = (
        "FontName=DejaVu Sans,FontSize=24,PrimaryColour=&H00FFFF&,"
        "OutlineColour=&H80000000&,Bold=-1,Outline=3,Shadow=1,Alignment=5,MarginV=380"
    )
    audio_input = audio_path
    mixed_path = None

    if music_path and os.path.exists(music_path):
        mixed_path = audio_path.replace(".mp3", "_mix.mp3")
        try:
            subprocess.run(
                [
                    "ffmpeg", "-y", "-i", audio_path, "-i", music_path,
                    "-filter_complex", "[1:a]volume=0.15[bg];[0:a][bg]amix=inputs=2:duration=first",
                    "-c:a", "libmp3lame", mixed_path,
                ],
                check=True,
                capture_output=True,
            )
            if os.path.exists(mixed_path):
                audio_input = mixed_path
        except Exception as e:
            print("MIX ERROR:", e)

    safe_srt = os.path.basename(srt_path)
    cwd = os.path.dirname(srt_path) or "."

    cmd = [
        "ffmpeg", "-y", "-loop", "1", "-i", image_path, "-i", audio_input,
        "-vf", f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,subtitles={safe_srt}:force_style='{style}'",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", out_path,
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, cwd=cwd)
        return os.path.exists(out_path)
    except Exception as e:
        print("FFMPEG ERROR:", e)
        return False
    finally:
        if mixed_path and os.path.exists(mixed_path):
            try:
                os.remove(mixed_path)
            except Exception:
                pass


# ---------- 8. ХЕНДЛЕРЛЕР ----------
@dp.message(Command("start"))
async def start(m: types.Message):
    await m.answer(
        f"👋 Салам! {SERIES_NAME} сериалына кош келдиң!\n\n"
        f"💔 Айдана менен Эмирдин окуясы\n"
        f"📱 Формат: 1080x1920 Shorts\n\n"
        f"1-сериядан баштайлыбы? 👇",
        reply_markup=main_kb(),
    )


@dp.message(F.text == "ℹ️ Сериал жөнүндө")
async def about(m: types.Message):
    await m.answer(
        f"{SERIES_NAME}\n\n👧 {MAIN_HERO}\n👦 {HERO2}\n🏙️ {SETTING}\n\n"
        f"Сюжет: Айдана эски шкафтан 3 жыл мурун жазылган кат табат. "
        f"Ал кат анын бүт жашоосун өзгөртөт."
    )


@dp.message(F.text == "❤️ Жазылуу")
async def sub(m: types.Message):
    cur.execute("INSERT OR REPLACE INTO subs VALUES (?,1)", (m.from_user.id,))
    conn.commit()
    await m.answer("❤️ Рахмат! Жаңы серия чыкканда сага кабар берем!")


@dp.message(F.text == "🎮 Mini App")
async def mini_app_info(m: types.Message):
    if MINI_APP_URL:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Шилтемени ачуу", url=MINI_APP_URL)]]
        )
        await m.answer("Mini App шилтемеси:", reply_markup=kb)
    else:
        await m.answer("Mini App URL азырынча коюла элек (`MINI_APP_URL`).")


@dp.message(F.text == "📜 1-сериядан баштоо")
async def ep1(m: types.Message):
    cur.execute("INSERT OR REPLACE INTO progress VALUES (?,1)", (m.from_user.id,))
    conn.commit()
    await send_episode(m, get_episode(1))


@dp.message(F.text == "▶️ Кийинки серия")
async def next_ep(m: types.Message):
    cur.execute("SELECT episode FROM progress WHERE user_id=?", (m.from_user.id,))
    row = cur.fetchone()
    nxt = (row[0] + 1) if row else 1
    if nxt > 10:
        nxt = 1
    cur.execute("INSERT OR REPLACE INTO progress VALUES (?,?)", (m.from_user.id, nxt))
    conn.commit()
    await send_episode(m, get_episode(nxt))


async def send_episode(m: types.Message, ep: dict):
    uid = m.from_user.id
    await m.answer(f"🎬 {ep['title']} жасалып жатат...")

    base = os.path.join(WORK_DIR, f"ak_{uid}_{ep['num']}")
    img = base + "_cover.jpg"
    audio = base + "_voice.mp3"
    srt = base + "_subs.srt"
    video = base + "_final.mp4"
    music = "music.mp3"

    ok_img = await asyncio.to_thread(make_anime_image, ep, img)
    ok_voice = await make_voice(ep["script"], audio)
    dur = get_audio_duration(audio, fallback=45.0) if ok_voice else 45.0
    await asyncio.to_thread(make_subtitles, ep["script"], dur, srt)

    ok_video = False
    if ok_img and ok_voice:
        ok_video = await asyncio.to_thread(
            make_video, img, audio, srt, video, music if os.path.exists(music) else None
        )

    if ok_video and os.path.exists(video):
        await m.answer_video(
            video=types.FSInputFile(video),
            caption=f"🎬 {ep['title']}\n{ep['hook']}",
        )
    elif ok_voice and os.path.exists(audio):
        await m.answer_voice(voice=types.FSInputFile(audio), caption=f"🔊 {ep['title']}")
    else:
        await m.answer("⚠️ Видео же үн түзүүдө ката чыкты. Render логдорун текшерип көр.")


async def main():
    print("Akirky Kat Bot ishtep jatat...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
