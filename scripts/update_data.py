#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自動更新 data.js 靜態快照（由 GitHub Actions 定時執行）。

從 Google Sheet gviz 端點抓「基板現況」與「6012 使用紀錄」，
用與 index.html 相同的欄位對應邏輯（findCol 名稱比對）重建
window.INVENTORY_DATA，寫回 data.js。

寫入條件（避免無意義的 commit 噪音）：
  1. 資料內容有變化；或
  2. 資料沒變，但既有 generated 時間已超過 24 小時（心跳更新，
     讓「靜態快照 · 時間」不會看起來太舊，也維持 repo 活動避免
     GitHub 停用排程）。
"""
import json
import re
import sys
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

SHEET_ID   = "1lNGJ9hGziZYXHfUNbLFSqkyZB0bUFa0APvZL1QDbuSA"
BLANKS_GID = "0"          # 基板現況分頁
G6012_GID  = "57603327"   # 6012 使用紀錄分頁
DATA_JS    = Path(__file__).resolve().parent.parent / "data.js"
TZ         = ZoneInfo("Asia/Taipei")
HEARTBEAT_HOURS = 24

HEADER = (
    "// 基板庫存資料靜態快照（GitHub Actions 定時自動產生，scripts/update_data.py）\n"
    "// 來源產生時間見 INVENTORY_DATA.generated\n"
    "// blanks: 基板現況；s6012: 6012 基板使用紀錄\n"
)


def gviz_rows(sheet_id, gid):
    """等同 index.html 的 fetchGVizJSON + gvizToRows：回傳 [headers, ...rows]"""
    url = (f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq"
           f"?gid={gid}&tqx=out:json")
    raw = urllib.request.urlopen(url, timeout=30).read().decode("utf-8")
    m = re.search(r"setResponse\((.*)\);?\s*$", raw, re.S)
    if not m:
        raise RuntimeError("gviz 回應格式異常（Sheet 可能未開放連結檢視）")
    table = json.loads(m.group(1)).get("table")
    if not table:
        raise RuntimeError("SHEET_NOT_PUBLIC")
    cols = table["cols"]
    headers = [(c.get("label") or "").strip() for c in cols]
    rows = [headers]
    for row in table.get("rows", []):
        cs = row.get("c") or []
        cells = []
        for i, col in enumerate(cols):
            c2 = cs[i] if i < len(cs) else None
            if not c2 or c2.get("v") is None:
                cells.append("")
                continue
            if col.get("type", "") in ("datetime", "date", "timeofday"):
                cells.append(c2.get("f") or "")
            else:
                v = c2["v"]
                # 模擬 JS String(v)：整數值浮點數不留 .0
                if isinstance(v, float) and v.is_integer():
                    v = int(v)
                cells.append(str(v))
        rows.append(cells)
    while len(rows) > 1 and all(not c for c in rows[-1]):
        rows.pop()
    return rows


def find_col(headers, keywords):
    """等同 index.html findCol：先全等、後包含（皆不分大小寫）"""
    lh = [(h or "").lower().strip() for h in headers]
    for kw in keywords:
        k = kw.lower()
        if k in lh:
            return lh.index(k)
    for kw in keywords:
        k = kw.lower()
        for i, h in enumerate(lh):
            if k in h:
                return i
    return -1


def cell(row, i):
    return str(row[i]) if (i >= 0 and i < len(row) and row[i] is not None) else ""


def map_blanks(rows):
    H = rows[0] if rows else []
    cS  = find_col(H, ["規格", "size", "尺寸"])
    cL  = find_col(H, ["metal lot", "批號", "lot"])
    cW  = find_col(H, ["庫別", "倉庫", "warehouse"])
    cC  = find_col(H, ["載具", "carrier"])
    cP  = find_col(H, ["使用目的", "目的", "purpose"])
    cU  = find_col(H, ["用途"])
    cPN = find_col(H, ["品號", "part no", "item no"])
    cN  = find_col(H, ["備註", "note"])
    cT  = find_col(H, ["板厚", "thickness", "thk"])
    cE  = find_col(H, ["費用化", "exp"])
    out = []
    for r in rows[1:]:
        wh = cell(r, cW).strip()
        if wh not in ("A倉", "B倉"):
            continue
        out.append({
            "lot": cell(r, cL), "pn": cell(r, cPN), "spec": cell(r, cS),
            "wh": wh, "car": cell(r, cC), "thk": cell(r, cT),
            "use": cell(r, cU), "pur": cell(r, cP),
            "note": cell(r, cN), "exp": cell(r, cE),
        })
    return out


def map_6012(rows):
    H = rows[0] if rows else []
    hB = H[1] if len(H) > 1 else ""
    mu = re.search(r"未使用庫存[：:]\s*(\d+)\s*片", hB)
    ms = re.search(r"可報廢[：:]\s*(\d+)\s*片", hB)
    cEmp  = find_col(H, ["人員工號", "工號", "employee"])
    cTime = find_col(H, ["時間", "time"])
    cMth  = find_col(H, ["方式", "method", "type"])
    cMch  = find_col(H, ["機台", "machine"])
    cPat  = find_col(H, ["描畫 pattern", "pattern", "描畫"])
    cPM   = find_col(H, ["pm 項目", "pm項目", "pm"])
    cNote = find_col(H, ["備註", "note"])
    out = []
    for r in rows[1:]:
        if not any(str(c or "").strip() for c in r):
            continue
        out.append({
            "emp": cell(r, cEmp), "time": cell(r, cTime),
            "mth": cell(r, cMth), "mch": cell(r, cMch),
            "pat": cell(r, cPat), "pm": cell(r, cPM), "note": cell(r, cNote),
        })
    return {
        "unused": int(mu.group(1)) if mu else None,
        "scrap": int(ms.group(1)) if ms else None,
        "rows": out,
    }


def main():
    new_payload = {
        "blanks": map_blanks(gviz_rows(SHEET_ID, BLANKS_GID)),
        "s6012": map_6012(gviz_rows(SHEET_ID, G6012_GID)),
    }
    if not new_payload["blanks"]:
        raise RuntimeError("抓到 0 筆基板資料，放棄寫入（避免覆蓋成空快照）")

    old_payload, old_generated = None, None
    if DATA_JS.exists():
        src = DATA_JS.read_text(encoding="utf-8")
        m = re.search(r"window\.INVENTORY_DATA\s*=\s*(\{.*\});?\s*$", src, re.S)
        if m:
            old = json.loads(m.group(1))
            old_generated = old.pop("generated", None)
            old_payload = old

    now = datetime.now(TZ)
    changed = (old_payload != new_payload)
    stale = True
    if old_generated:
        try:
            age = now - datetime.strptime(old_generated, "%Y/%m/%d %H:%M").replace(tzinfo=TZ)
            stale = age.total_seconds() > HEARTBEAT_HOURS * 3600
        except ValueError:
            pass

    if not changed and not stale:
        print(f"資料無變化且快照未逾 {HEARTBEAT_HOURS}h（{old_generated}），不更新")
        return

    data = {"generated": now.strftime("%Y/%m/%d %H:%M"), **new_payload}
    body = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    DATA_JS.write_text(HEADER + "window.INVENTORY_DATA = " + body + ";\n",
                       encoding="utf-8")
    print(f"data.js 已更新（{'資料變更' if changed else '心跳更新'}）："
          f"blanks {len(new_payload['blanks'])} 筆、"
          f"6012 rows {len(new_payload['s6012']['rows'])} 筆")


if __name__ == "__main__":
    sys.exit(main())
