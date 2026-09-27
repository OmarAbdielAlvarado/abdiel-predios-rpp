#!/usr/bin/env python3
# AbdielBusca_Bot: ubicacion -> /buscar_predio_cercano (form) -> dueno. Grupos: solo log.
import os, json, time, urllib.request, urllib.parse
TOKEN = os.environ["TG_BOT_TOKEN"]  # ROTAR (expuesto)
API = f"https://api.telegram.org/bot{TOKEN}"
EP = "http://localhost:5001/buscar_predio_cercano"
ALLOWED = {int(x) for x in os.environ.get("TG_CHAT_IDS", "").replace(" ", "").split(",") if x}

def tg(met, **kw):
    r = urllib.request.Request(f"{API}/{met}", data=json.dumps(kw).encode(),
                               headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(r, timeout=60).read())

def dueno(lat, lon):
    if os.environ.get("DEMO") == "1":
        import csv
        ruta = os.path.join(os.path.dirname(__file__), "mexsim_clientes_demo.csv")
        filas = list(csv.DictReader(open(ruta, encoding="utf-8-sig")))
        best, bd = None, 9e9
        for p in filas:
            d = (float(p["Latitud"])-lat)**2 + (float(p["Longitud"])-lon)**2
            if d < bd: bd, best = d, p
        if not best: return f"Sin datos demo ({len(filas)} filas leidas)"
        return f"""[DEMO] {best['Calle']}, {best['Ciudad']}
Cliente: {best['Cliente']} | Pedido: {best['Pedido']}
Tel: {best['Telefono']} | Folio {best['Folio']}"""
    try:
        d = urllib.parse.urlencode({"coordenadas": f"{lat},{lon}"}).encode()
        r = urllib.request.Request(EP, data=d, headers={"Content-Type": "application/x-www-form-urlencoded"})
        out = json.loads(urllib.request.urlopen(r, timeout=25).read())
        res = (out or {}).get("resultados") or []
        if not res: return str((out or {}).get("error") or "Sin resultados.")
        p = res[0]
        num = p.get("Número") or p.get("Numero") or "?"
        return f"""[REAL] {p.get('Calle','?')} {num}, {p.get('Colonia','?')}, {p.get('Municipio','?')}
Propietario: {p.get('Propietario','?')}
Folio {p.get('Folio Real','?')} | Sup {p.get('Superficie Construida (m²)','?')}"""
    except Exception as e:
        return f"Error: {e}"

def main():
    off = 0
    print(f"Abdiel predios arriba. Whitelist: {ALLOWED or 'VACIA'}", flush=True)
    while True:
        try:
            ups = tg("getUpdates", offset=off, timeout=50).get("result", [])
        except Exception as e:
            print("getUpdates reintenta:", e, flush=True); time.sleep(3); continue
        for u in ups:
            off = u["update_id"] + 1
            m = u.get("message") or {}
            cid = (m.get("chat") or {}).get("id")
            if cid is None: continue
            if cid not in ALLOWED:
                tag = "GRUPO" if cid < 0 else "SIN AUTORIZAR"
                print(f"[{tag}] chat_id={cid} de={m.get('from',{}).get('first_name')} texto={str(m.get('text'))[:50]}", flush=True)
                if cid > 0:
                    tg("sendMessage", chat_id=cid, text="No autorizado.")
                continue
            loc = m.get("location")
            if loc:
                tg("sendMessage", chat_id=cid, text=dueno(loc["latitude"], loc["longitude"]))
            elif cid > 0:
                tg("sendMessage", chat_id=cid, text="Manda ubicacion: clip > Ubicacion.")

if __name__ == "__main__":
    main()
