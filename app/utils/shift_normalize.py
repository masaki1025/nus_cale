from typing import Any, Dict, List


def norm_name(name: str) -> str:
    """氏名の簡易正規化（全角スペース等を除去）。"""
    if name is None:
        return ""
    s = str(name).replace("　", " ").strip()
    return s


def norm_shift(s: str) -> str:
    """勤務表記の簡易正規化（略記や表記ゆれを吸収）。"""
    if not s:
        return ""
    s = str(s).strip()
    s = s.replace("　", " ").strip()
    if s in ("公", "休", "公休"):
        return "公休"
    if s in ("日", "日勤"):
        return "日勤"
    if s in ("準", "準夜"):
        return "準夜"
    if s in ("深", "深夜"):
        return "深夜"
    return s


def _looks_like_date(key: str) -> bool:
    if not key or not isinstance(key, str) or len(key) != 10:
        return False
    parts = key.split("-")
    if len(parts) != 3:
        return False
    y, m, d = parts
    return len(y) == 4 and len(m) == 2 and len(d) == 2 and y.isdigit() and m.isdigit() and d.isdigit()


def normalize_to_long(all_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """任意の行配列を縦持ち（name,date,shift）へ正規化する。

    - すでに縦持ち（name/date/shift）が揃っている行はそのまま正規化
    - 横持ち（先頭が氏名、以降が日付列）の行は、日付キーを走査して展開
    - 勤務は簡易正規化し、公休や空白は除外
    """
    long_rows: List[Dict[str, Any]] = []
    for row in all_rows or []:
        keys = list(row.keys())

        # 氏名の取得（候補キー → 最初の非日付キー）
        name_val = None
        for nk in ("name", "氏名", "看護師", "ナース", "スタッフ", "従業員", "担当", ""):
            if nk in row and str(row.get(nk, "")).strip() != "":
                name_val = norm_name(row.get(nk, ""))
                break
        if name_val is None:
            for k in keys:
                if not _looks_like_date(str(k)):
                    name_val = norm_name(row.get(k, ""))
                    break

        # 縦持ち（name/date/shift）が揃っている場合
        if {"date", "shift"}.issubset(set(keys)):
            d = str(row.get("date", "")).strip()
            sh = norm_shift(row.get("shift", ""))
            if name_val and d and sh and sh != "公休":
                long_rows.append({"name": name_val, "date": d, "shift": sh})
            continue

        # 横持ち: 日付キーを走査
        if name_val:
            for k in keys:
                if _looks_like_date(str(k)):
                    d = str(k)
                    sh = norm_shift(row.get(k, ""))
                    if sh and sh != "公休":
                        long_rows.append({"name": name_val, "date": d, "shift": sh})

    return long_rows

