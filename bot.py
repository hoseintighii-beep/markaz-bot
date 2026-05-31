import json
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler

BOT_TOKEN = "8834769760:AAHskqhlOZ6lpymVyFg-H88uZmEUtZXFhMw"
AT_TOKEN  = "patt88vFOyn3DUITo.ac69cdd48cba67c9b42ba3c9af296050912eaca07f82eb0191c058b2a7f58ba8"
AT_BASE   = "apprOFBLKmXIeOmAu"
AT_TABLE  = "tblHZaxddZMRuhxyu"
SITE_URL  = "https://tomato-rosana-12.tiiny.site"

STEPS = [
    "عقد قرارداد",
    "تایید اولیه مدارک",
    "تکمیل مدارک",
    "تشکیل کارگروه تخصصی",
    "تشکیل پرونده در اداره مهاجرت اسپانیا",
    "سفر اول به اسپانیا",
    "انجام امور اداری اسپانیا",
    "بازگشت از سفر",
    "صدور اقامت و کد ملی اسپانیایی"
]

SMS = [
    "سلام {n} عزیز 🙏\nقرارداد با مرکز علوم ثبت شد.\nکد پرونده: {c}\n— مرکز علوم",
    "سلام {n} جان 👋\nمدارک اولیه تایید شد.\n— مرکز علوم",
    "سلام {n} عزیز 📋\nنوبت تکمیل مدارک رسیده.\n— مرکز علوم",
    "سلام {n} 🎯\nپرونده وارد کارگروه تخصصی شد.\n— مرکز علوم",
    "سلام {n} 📁\nپرونده در اداره مهاجرت اسپانیا تشکیل شد!\n— مرکز علوم",
    "سلام {n} ✈️\nوقت سفر اول به اسپانیا رسید! سفر خوش 🙏\n— مرکز علوم",
    "سلام {n} 🏛️\nامور اداری اسپانیا شروع شده.\n— مرکز علوم",
    "سلام {n} 🏠\nخوش برگشتی! پرونده در مرحله نهاییه.\n— مرکز علوم",
    "سلام {n} 🎉\nتبریک! اقامت اسپانیا صادر شد ❤️\n— مرکز علوم"
]

states = {}

# ===== Airtable =====
def at_url(rec_id=""):
    base = f"https://api.airtable.com/v0/{AT_BASE}/{AT_TABLE}"
    return f"{base}/{rec_id}" if rec_id else base

def at_h():
    return {"Authorization": f"Bearer {AT_TOKEN}", "Content-Type": "application/json"}

def get_all():
    r = requests.get(at_url(), headers=at_h())
    out = []
    for rec in r.json().get("records", []):
        f = rec["fields"]
        out.append({
            "id": f.get("id",""),
            "rid": rec["id"],
            "name": f.get("name",""),
            "phone": f.get("phone","-"),
            "startDate": f.get("startDate","-"),
            "step": int(f.get("activeStep",0)),
            "note": f.get("note",""),
            "tgid": f.get("tgid","")
        })
    return out

def get_by_id(cid):
    for c in get_all():
        if c["id"].upper() == cid.upper():
            return c
    return None

def add_client(name, phone, date, note=""):
    all_c = get_all()
    cid = f"MO-{len(all_c)+1:03d}"
    data = {"fields": {"id": cid, "name": name, "phone": phone, "startDate": date, "activeStep": 0, "note": note, "tgid": ""}}
    r = requests.post(at_url(), headers=at_h(), json=data)
    if r.status_code in [200,201]:
        return cid, r.json()["id"]
    return None, None

def set_step(rid, step):
    r = requests.patch(at_url(rid), headers=at_h(), json={"fields": {"activeStep": step}})
    return r.status_code in [200,201]

def set_tgid(rid, tgid):
    requests.patch(at_url(rid), headers=at_h(), json={"fields": {"tgid": str(tgid)}})

# ===== Telegram =====
def tg(method, data):
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/{method}", json=data)

def send(cid, text, kbd=None):
    d = {"chat_id": cid, "text": text, "parse_mode": "HTML"}
    if kbd: d["reply_markup"] = kbd
    tg("sendMessage", d)

def client_card(cid, c):
    p = round(((c["step"]+1)/len(STEPS))*100)
    bar = "█"*(p//10) + "░"*(10-p//10)
    t = f"📋 <b>{c['name']}</b>\n🔑 کد: {c['id']}\n📱 {c['phone']}\n📅 {c['startDate']}\n\n"
    t += f"📊 {p}%  {bar}\n\n"
    for i,s in enumerate(STEPS):
        if i < c["step"]: t += f"✅ {i+1}. {s}\n"
        elif i == c["step"]: t += f"🔵 {i+1}. {s}  ← فعال\n"
        else: t += f"⬜ {i+1}. {s}\n"
    t += f"\n🔗 {SITE_URL}?track={c['id']}"
    send(cid, t)

# ===== Handler =====
def handle(msg):
    cid = msg["chat"]["id"]
    uid = msg["from"]["id"]
    txt = msg.get("text","").strip()
    st  = states.get(cid, {})

    if txt == "/start":
        send(cid,
            "سلام به ربات مرکز علوم خوش اومدی 👋\n\n"
            "<b>ادمین:</b>\n"
            "/add — مشتری جدید\n"
            "/list — لیست پرونده‌ها\n"
            "/next [کد] — مرحله بعد\n"
            "/find [کد] — جزئیات پرونده\n"
            "/sms [کد] — متن پیامک\n"
            "/myid — آیدی شما\n\n"
            "<b>مشتری:</b>\n"
            "کد پرونده‌ات رو بفرست (مثلاً MO-001)"
        )
        return

    if txt == "/myid":
        send(cid, f"آیدی تلگرام شما:\n<code>{uid}</code>")
        return

    if txt == "/list":
        clients = get_all()
        if not clients:
            send(cid, "هیچ پرونده‌ای ثبت نشده.")
            return
        t = "📋 <b>پرونده‌ها:</b>\n\n"
        for c in clients:
            p = round(((c["step"]+1)/len(STEPS))*100)
            t += f"🔹 {c['id']} — {c['name']} — {p}% — {STEPS[c['step']]}\n"
        send(cid, t)
        return

    if txt.startswith("/find"):
        parts = txt.split()
        if len(parts) < 2: send(cid, "مثال: /find MO-001"); return
        c = get_by_id(parts[1])
        if c: client_card(cid, c)
        else: send(cid, "پرونده یافت نشد.")
        return

    if txt.startswith("/next"):
        parts = txt.split()
        if len(parts) < 2: send(cid, "مثال: /next MO-001"); return
        c = get_by_id(parts[1])
        if not c: send(cid, "پرونده یافت نشد."); return
        if c["step"] >= len(STEPS)-1: send(cid, "🎉 این پرونده تکمیل شده!"); return
        ns = c["step"] + 1
        if set_step(c["rid"], ns):
            c["step"] = ns
            send(cid, f"✅ پرونده {c['id']} — مرحله {ns+1}:\n<b>{STEPS[ns]}</b>")
            if c["tgid"]:
                sms = SMS[ns].replace("{n}", c["name"].split()[0]).replace("{c}", c["id"])
                sms += f"\n\n🔗 مشاهده پرونده:\n{SITE_URL}?track={c['id']}"
                send(c["tgid"], sms)
                send(cid, "📨 پیام به مشتری ارسال شد.")
            else:
                send(cid, "⚠️ مشتری هنوز ربات رو استارت نزده.")
        else:
            send(cid, "خطا در ذخیره.")
        return

    if txt.startswith("/sms"):
        parts = txt.split()
        if len(parts) < 2: send(cid, "مثال: /sms MO-001"); return
        c = get_by_id(parts[1])
        if not c: send(cid, "پرونده یافت نشد."); return
        sms = SMS[c["step"]].replace("{n}", c["name"].split()[0]).replace("{c}", c["id"])
        send(cid, f"متن پیامک:\n\n{sms}")
        return

    if txt == "/add":
        states[cid] = {"s": "name"}
        send(cid, "نام کامل مشتری:")
        return

    if st.get("s") == "name":
        states[cid] = {"s": "phone", "name": txt}
        send(cid, f"✅ نام: {txt}\n\nموبایل:")
        return

    if st.get("s") == "phone":
        states[cid]["phone"] = txt
        states[cid]["s"] = "date"
        send(cid, f"✅ موبایل: {txt}\n\nتاریخ شروع (مثلاً ۱۰ خرداد ۱۴۰۵):")
        return

    if st.get("s") == "date":
        states[cid]["date"] = txt
        states[cid]["s"] = "confirm"
        s = states[cid]
        send(cid,
            f"تایید اطلاعات:\n\n"
            f"👤 {s['name']}\n📱 {s['phone']}\n📅 {s['date']}\n\n"
            f"/confirm برای ثبت\n/cancel برای لغو"
        )
        return

    if txt == "/confirm" and st.get("s") == "confirm":
        s = states.pop(cid)
        cid_new, rid = add_client(s["name"], s["phone"], s["date"])
        if cid_new:
            send(cid,
                f"✅ ثبت شد!\n\nکد: <b>{cid_new}</b>\n"
                f"لینک مشتری:\n{SITE_URL}?track={cid_new}\n\n"
                f"این لینک رو به مشتری بفرست 👆"
            )
        else:
            send(cid, "خطا در ثبت. دوباره امتحان کن.")
        return

    if txt == "/cancel":
        states.pop(cid, None)
        send(cid, "لغو شد.")
        return

    if txt.upper().startswith("MO-"):
        c = get_by_id(txt.upper())
        if c:
            if str(uid) != c["tgid"]:
                set_tgid(c["rid"], uid)
            p = round(((c["step"]+1)/len(STEPS))*100)
            bar = "█"*(p//10) + "░"*(10-p//10)
            t = f"سلام {c['name'].split()[0]} عزیز 👋\n\n"
            t += f"📊 پیشرفت: {p}%  {bar}\n\n"
            for i,s in enumerate(STEPS):
                if i < c["step"]: t += f"✅ {s}\n"
                elif i == c["step"]: t += f"🔵 {s}  ← الان اینجایی\n"
                else: t += f"⬜ {s}\n"
            t += f"\n🔗 {SITE_URL}?track={c['id']}"
            send(cid, t)
        else:
            send(cid, "کد پرونده اشتباهه. مثال: MO-001")
        return

    send(cid, "کد پرونده‌ات رو بفرست یا /start برای راهنما")

class H(BaseHTTPRequestHandler):
    def do_POST(self):
        n = int(self.headers.get("Content-Length",0))
        body = self.rfile.read(n)
        try:
            u = json.loads(body)
            if "message" in u:
                handle(u["message"])
        except Exception as e:
            print("err:", e)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
    def log_message(self, *a): pass

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8080))
    print(f"Starting on port {port}")
    HTTPServer(("0.0.0.0", port), H).serve_forever()
