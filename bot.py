import json
import requests
import os
from http.server import HTTPServer, BaseHTTPRequestHandler

BOT_TOKEN = "8834769760:AAHskqhlOZ6lpymVyFg-H88uZmEUtZXFhMw"
AT_TOKEN  = os.environ.get("AT_TOKEN", "patt88vFOyn3DUITo.ac69cdd48cba67c9b42ba3c9af296050912eaca07f82eb0191c058b2a7f58ba8")
AT_BASE   = "apprOFBLKmXIeOmAu"
AT_TABLE  = "tblHZaxddZMRuhxyu"
SITE_URL  = "https://tomato-rosana-12.tiiny.site"

print(f"AT_TOKEN starts with: {AT_TOKEN[:20]}...")

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
        print(f"GET all status: {r.status_code}")
        if r.status_code != 200:
            print(f"GET all error: {r.text}")
            return []
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
        print(f"get_all exception: {e}")
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
        print(f"Adding client: {data}")
        r = requests.post(at_url(), headers=at_h(), json=data, timeout=10)
        print(f"Add status: {r.status_code}, response: {r.text[:200]}")
        if r.status_code in [200,201]:
            return cid, r.json()["id"]
        return None, None
    except Exception as e:
        print(f"add_client exception: {e}")
        return None, None

def set_step(rid, step):
    try:
        r = requests.patch(at_url(rid), headers=at_h(), json={"fields":{"activeStep":step}}, timeout=10)
        print(f"set_step status: {r.status_code}")
        return r.status_code in [200,201]
    except Exception as e:
        print(f"set_step exception: {e}")
        return False

def set_tgid(rid, tgid):
    try:
        requests.patch(at_url(rid), headers=at_h(), json={"fields":{"tgid":str(tgid)}}, timeout=10)
    except: pass

def tg(method, data):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/{method}", json=data, timeout=10)
    except Exception as e:
        print(f"tg error: {e}")

def send(cid, text):
    tg("sendMessage", {"chat_id":cid,"text":text,"parse_mode":"HTML"})

def handle(msg):
    cid = msg["chat"]["id"]
    uid = msg["from"]["id"]
    txt = msg.get("text","").strip()
    st  = states.get(cid, {})
    print(f"msg from {uid}: {txt}")

    if txt == "/start":
        send(cid, "سلام به ربات مرکز علوم خوش اومدی 👋\n\n/add — مشتری جدید\n/list — لیست پرونده‌ها\n/next [کد] — مرحله بعد\n/find [کد] — جزئیات\n/myid — آیدی شما")
        return

    if txt == "/myid":
        send(cid, f"آیدی: <code>{uid}</code>")
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
        t = f"📋 <b>{c['name']}</b>\n🔑 {c['id']}\n📱 {c['phone']}\n📅 {c['startDate']}\n📊 {p}%\n\n✅ مرحله: {STEPS[c['step']]}"
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
            send(cid, f"✅ {c['id']} — مرحله {ns+1}:\n<b>{STEPS[ns]}</b>")
            if c["tgid"]:
                sms = SMS[ns].replace("{n}",c["name"].split()[0]).replace("{c}",c["id"])
                sms += f"\n\n🔗 {SITE_URL}?track={c['id']}"
                send(c["tgid"], sms)
        else:
            send(cid,"خطا در ذخیره.")
        return

    if txt == "/add":
        states[cid] = {"s":"name"}
        send(cid,"نام کامل مشتری:")
        return

    if st.get("s")=="name":
        states[cid] = {"s":"phone","name":txt}
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
            send(cid,f"✅ ثبت شد!\nکد: <b>{cid_new}</b>\n\nلینک مشتری:\n{SITE_URL}?track={cid_new}")
        else:
            send(cid,"خطا در ثبت. دوباره امتحان کن /add")
        return

    if txt=="/cancel":
        states.pop(cid,None)
        send(cid,"لغو شد.")
        return

    if txt.upper().startswith("MO-"):
        c=get_by_id(txt.upper())
        if c:
            if str(uid)!=c["tgid"]: set_tgid(c["rid"],uid)
            p=round(((c["step"]+1)/len(STEPS))*100)
            bar="█"*(p//10)+"░"*(10-p//10)
            t=f"سلام {c['name'].split()[0]} عزیز 👋\n\n📊 {p}%  {bar}\n\n"
            for i,s in enumerate(STEPS):
                if i<c["step"]: t+=f"✅ {s}\n"
                elif i==c["step"]: t+=f"🔵 {s}  ← الان\n"
                else: t+=f"⬜ {s}\n"
            t+=f"\n🔗 {SITE_URL}?track={c['id']}"
            send(cid,t)
        else:
            send(cid,"کد اشتباهه. مثال: MO-001")
        return

    send(cid,"دستور نامعتبر. /start برای راهنما")

class H(BaseHTTPRequestHandler):
    def do_POST(self):
        n=int(self.headers.get("Content-Length",0))
        body=self.rfile.read(n)
        try:
            u=json.loads(body)
            if "message" in u: handle(u["message"])
        except Exception as e:
            print(f"handler error: {e}")
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
    def log_message(self,*a): pass

if __name__=="__main__":
    port=int(os.environ.get("PORT",8080))
    print(f"Starting on port {port}")
    HTTPServer(("0.0.0.0",port),H).serve_forever()
