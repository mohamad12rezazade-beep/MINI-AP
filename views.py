import os, json
import psycopg2
from psycopg2.extras import RealDictCursor
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from init_data_py import InitData

DATABASE_URL = os.environ.get("SUPABASE_URL") or os.environ["DATABASE_URL"]
BOT_TOKEN = os.environ["BOT_TOKEN"]

def _user(uid):
    c = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    try:
        with c.cursor() as cur:
            cur.execute("select * from users where telegram_id=%s", (uid,))
            return cur.fetchone()
    finally: c.close()

def _upd(uid, val):
    c = psycopg2.connect(DATABASE_URL)
    try:
        with c.cursor() as cur:
            cur.execute("update users set balance_ton=%s where telegram_id=%s", (val, uid))
            c.commit()
    finally: c.close()

def _validate(req):
    d = json.loads(req.body)
    try:
        p = InitData.parse(d["initData"]).validate(BOT_TOKEN)
        return p.user.id
    except: return None

@csrf_exempt
def balance(req):
    uid = _validate(req)
    if not uid: return JsonResponse({"error":"auth"}, status=403)
    u = _user(uid)
    return JsonResponse({"ton": float(u["balance_ton"] or 0) if u else 0})

@csrf_exempt
def bet(req):
    uid = _validate(req)
    if not uid: return JsonResponse({"error":"auth"}, status=403)
    d = json.loads(req.body)
    amt, mult, win = float(d["amount"]), float(d.get("multiplier", 0)), d.get("win", False)
    u = _user(uid)
    bal = float(u["balance_ton"] or 0)
    if bal < amt: return JsonResponse({"error":"balance"}, status=400)
    new_bal = bal - amt + (amt * mult if win else 0)
    _upd(uid, new_bal)
    return JsonResponse({"balance": new_bal})
