import json
import requests
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

BOT_TOKEN = "8834769760:AAHskqhlOZ6lpymVyFg-H88uZmEUtZXFhMw"
AT_TOKEN  = os.environ.get("AT_TOKEN", "patt88vFOyn3DUITo.ac69cdd48cba67c9b42ba3c9af296050912eaca07f82eb0191c058b2a7f58ba8")
AT_BASE   = "apprOFBLKmXIeOmAu"
AT_TABLE  = "tblHZaxddZMRuhxyu"
SITE_URL  = "https://tomato-rosana-12.tiiny.site"
ADMIN_ID  = 1657275993

STEPS = [
    "عقد قرارداد","تایید اولیه مدارک","تکمیل مدارک",
    "تشکیل کارگروه تخصصی","تشکیل پرونده در اداره مهاجرت اسپانیا",
    "سفر اول به اسپانیا","انجام امور اداری اسپانیا",
    "بازگشت از سفر","صدور اقامت و کد ملی اسپانیایی"
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

def at_url(rid=""):
    base = f"https://api.airtable.com/v0/{AT_BASE}/{AT_TABLE}"
    return f"{base}/{rid}" if rid else base

def at_h():
    return {"Authorization": f"Bearer {AT_TOKEN}", "Content-Type": "application/json"}

def get_all():
    try:
        r = requests.get(at_url(), headers=at_h(), timeout=10)
        if r.status_code != 200: return []
        out = []
        for rec in r.json().get("records", []):
            f = rec["fields"]
            out.append({
                "id": f.get("id",""), "rid": rec["id"],
                "name": f.get("name",""), "phone": f.get("phone","-"),
                "startDate": f.get("startDate","-"),
                "step": int(f.get("activeStep",0)),
                "note": f.get("note",""), "tgid": f.get("tgid","")
            })
        return out
    except Exception as e:
        print(f"get_all error: {e}")
        return []

def get_by_id(cid):
    for c in get_all():
        if c["id"].upper() == cid.upper():
            return c
    return None

def add_client(name, phone, date, note=""):
    try:
        all_c = get_all()
        cid = f"MO-{len(all_c)+1:03d}"
        data = {"fields": {
            "id": cid, "name": name, "phone": phone,
            "startDate": date, "activeStep": 0,
            "note": note, "tgid": ""
        }}
        r = requests.post(at_url(), headers=at_h(), json=data, timeout=10)
        if r.status_code in [200,201]:
            return cid, r.json()["id"]
        return None, None
    except Exception as e:
        print(f"add error: {e}")
        return None, None

def set_step(rid, step):
    try:
        r = requests.patch(at_url(rid), headers=at_h(), json={"fields":{"activeStep":step}}, timeout=10)
        return r.status_code in [200,201]
    except: return False

def set_tgid(rid, tgid):
    try:
        requests.patch(at_url(rid), headers=at_h(), json={"fields":{"tgid":str(tgid)}}, timeout=10)
    except: pass

def tg(method, data):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/{method}", json=data, timeout=10)
    except: pass

def send(cid, text):
    tg("sendMessage", {"chat_id":cid, "text":text, "parse_mode":"HTML"})

def handle(msg):
    cid = msg["chat"]["id"]
    uid = msg["from"]["id"]
    txt = msg.get("text","").strip()
    st  = states.get(cid, {})
    is_admin = (uid == ADMIN_ID)

    if txt == "/myid":
        send(cid, f"آیدی: <code>{uid}</code>")
        return

    if not is_admin:
        if txt.upper().startswith("MO-"):
            c = get_by_id(txt.upper())
            if c:
                if str(uid) != c["tgid"]: set_tgid(c["rid"], uid)
                p = round(((c["step"]+1)/len(STEPS))*100)
                bar = "█"*(p//10)+"░"*(10-p//10)
                t = f"سلام {c['name'].split()[0]} عزیز 👋\n\n📊 {p}%  {bar}\n\n"
                for i,s in enumerate(STEPS):
                    if i < c["step"]: t += f"✅ {s}\n"
                    elif i == c["step"]: t += f"🔵 {s}  ← الان\n"
                    else: t += f"⬜ {s}\n"
                t += f"\n🔗 {SITE_URL}?track={c['id']}"
                send(cid, t)
            else:
                send(cid, "کد اشتباهه. مثال: MO-001")
        else:
            send(cid, "سلام! کد پرونده‌ات رو بفرست.\nمثال: MO-001")
        return

    if txt == "/start":
        send(cid, "سلام حسین! 👋\n\n/add — مشتری جدید\n/list — لیست پرونده‌ها\n/find [کد] — جزئیات\n/next [کد] — مرحله بعد\n/sms [کد] — متن پیامک")
        return

    if txt == "/list":
        clients = get_all()
        if not clients: send(cid, "هیچ پرونده‌ای ثبت نشده."); return
        t = "📋 <b>پرونده‌ها:</b>\n\n"
        for c in clients:
            p = round(((c["step"]+1)/len(STEPS))*100)
            t += f"🔹 {c['id']} — {c['name']} — {p}%\n"
        send(cid, t)
        return

    if txt.startswith("/find"):
        parts = txt.split()
        if len(parts)<2: send(cid,"مثال: /find MO-001"); return
        c = get_by_id(parts[1])
        if not c: send(cid,"پرونده یافت نشد."); return
        p = round(((c["step"]+1)/len(STEPS))*100)
        t = f"📋 <b>{c['name']}</b>\n🔑 {c['id']}\n📱 {c['phone']}\n📅 {c['startDate']}\n📊 {p}%\n✅ {STEPS[c['step']]}"
        send(cid, t)
        return

    if txt.startswith("/next"):
        parts = txt.split()
        if len(parts)<2: send(cid,"مثال: /next MO-001"); return
        c = get_by_id(parts[1])
        if not c: send(cid,"پرونده یافت نشد."); return
        if c["step"]>=len(STEPS)-1: send(cid,"🎉 تکمیل شده!"); return
        ns = c["step"]+1
        if set_step(c["rid"],ns):
            send(cid, f"✅ {c['id']} مرحله {ns+1}:\n<b>{STEPS[ns]}</b>")
            if c["tgid"]:
                sms = SMS[ns].replace("{n}",c["name"].split()[0]).replace("{c}",c["id"])
                sms += f"\n\n🔗 {SITE_URL}?track={c['id']}"
                send(c["tgid"], sms)
                send(cid,"📨 پیام ارسال شد.")
            else:
                send(cid,"⚠️ مشتری هنوز ربات رو استارت نزده.")
        else:
            send(cid,"خطا در ذخیره.")
        return

    if txt.startswith("/sms"):
        parts = txt.split()
        if len(parts)<2: send(cid,"مثال: /sms MO-001"); return
        c = get_by_id(parts[1])
        if not c: send(cid,"پرونده یافت نشد."); return
        sms = SMS[c["step"]].replace("{n}",c["name"].split()[0]).replace("{c}",c["id"])
        send(cid, f"متن پیامک:\n\n{sms}")
        return

    if txt == "/add":
        states[cid] = {"s":"name"}
        send(cid,"نام کامل مشتری:")
        return

    if st.get("s")=="name":
        states[cid]={"s":"phone","name":txt}
        send(cid,f"✅ نام: {txt}\n\nموبایل:")
        return

    if st.get("s")=="phone":
        states[cid]["phone"]=txt
        states[cid]["s"]="date"
        send(cid,f"✅ موبایل: {txt}\n\nتاریخ شروع:")
        return

    if st.get("s")=="date":
        states[cid]["date"]=txt
        states[cid]["s"]="confirm"
        s=states[cid]
        send(cid,f"تایید:\n👤 {s['name']}\n📱 {s['phone']}\n📅 {s['date']}\n\n/confirm ثبت\n/cancel لغو")
        return

    if txt=="/confirm" and st.get("s")=="confirm":
        s=states.pop(cid)
        cid_new,rid=add_client(s["name"],s["phone"],s["date"])
        if cid_new:
            send(cid,f"✅ ثبت شد!\nکد: <b>{cid_new}</b>\n\nلینک مشتری:\n{SITE_URL}?track={cid_new}\n\nاین لینک رو به مشتری بفرست 👆")
        else:
            send(cid,"خطا در ثبت. /add دوباره امتحان کن.")
        return

    if txt=="/cancel":
        states.pop(cid,None)
        send(cid,"لغو شد.")
        return

    send(cid,"دستور نامعتبر. /start برای راهنما")


def json_response(handler, data, status=200):
    body = json.dumps(data, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


class H(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        action = params.get("action", [""])[0]
        cid    = params.get("id", [""])[0]

        if action == "getOne" and cid:
            c = get_by_id(cid)
            if c:
                json_response(self, {"success": True, "client": {
                    "id": c["id"], "name": c["name"],
                    "phone": c["phone"], "startDate": c["startDate"],
                    "activeStep": str(c["step"]), "note": c["note"]
                }})
            else:
                json_response(self, {"success": False, "error": "پرونده یافت نشد"})
        elif action == "getAll":
            clients = get_all()
            json_response(self, {"success": True, "clients": [
                {"id":c["id"],"name":c["name"],"phone":c["phone"],
                 "startDate":c["startDate"],"activeStep":str(c["step"]),"note":c["note"]}
                for c in clients
            ]})
        else:
            json_response(self, {"success": True, "status": "ok"})

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(n)
        try:
            u = json.loads(body)
            if "message" in u: handle(u["message"])
        except Exception as e:
            print(f"error: {e}")
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, *a): pass


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"Starting on port {port}")
    HTTPServer(("0.0.0.0", port), H).serve_forever()
