from typing import Any, Dict, List


def _norm_shift(s: str) -> str:
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


def _norm_name(name: str) -> str:
    if name is None:
        return ""
    s = str(name).replace("　", " ").strip()
    return s


def _looks_like_date(key: str) -> bool:
    """キーが YYYY-MM-DD のような日付に見えるかを判定する。"""
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
                name_val = _norm_name(row.get(nk, ""))
                break
        if name_val is None:
            for k in keys:
                if not _looks_like_date(str(k)):
                    name_val = _norm_name(row.get(k, ""))
                    break

        # 縦持ち（name/date/shift）が揃っている場合
        if {"date", "shift"}.issubset(set(keys)):
            d = str(row.get("date", "")).strip()
            sh = _norm_shift(row.get("shift", ""))
            if name_val and d and sh and sh != "公休":
                long_rows.append({"name": name_val, "date": d, "shift": sh})
            continue

        # 横持ち: 日付キーを走査
        if name_val:
            for k in keys:
                if _looks_like_date(str(k)):
                    d = str(k)
                    sh = _norm_shift(row.get(k, ""))
                    if sh and sh != "公休":
                        long_rows.append({"name": name_val, "date": d, "shift": sh})

    return long_rows


def pick_my_rows(all_shifts: List[Dict[str, Any]], my_name: str) -> List[Dict[str, Any]]:
    """全体のシフトから自分の行を抽出し、[{date, shift}] 形式に整形する。

    対応フォーマット:
    - 縦持ち: 行に name/date/shift がある場合 → そのまま抽出
    - 横持ち: 行に氏名と複数の日付列がある場合 → 日付キーを走査して抽出
    """
    my = _norm_name(my_name)
    if not my:
        return []

    out: List[Dict[str, Any]] = []
    for row in all_shifts or []:
        keys = list(row.keys())
        # 候補の氏名キーを推定
        name_keys = [
            "name", "氏名", "看護師", "ナース", "スタッフ", "従業員", "担当", "",
        ]
        name_val = None
        for nk in name_keys:
            if nk in row and str(row.get(nk, "")).strip() != "":
                name_val = _norm_name(row.get(nk, ""))
                break
        if name_val is None:
            # 見つからなければ最初の非日付キーを氏名とみなす
            for k in keys:
                if not _looks_like_date(str(k)):
                    name_val = _norm_name(row.get(k, ""))
                    break

        if name_val != my:
            continue

        # 縦持ち（name/date/shift）が揃っているケース
        if "date" in row and "shift" in row:
            d = str(row.get("date", "")).strip()
            sh = _norm_shift(row.get("shift", ""))
            if d and sh:
                out.append({"date": d, "shift": sh})
            continue

        # 横持ち: 日付キーを走査
        for k in keys:
            if _looks_like_date(str(k)):
                d = str(k)
                sh = _norm_shift(row.get(k, ""))
                if sh:
                    out.append({"date": d, "shift": sh})

    # 公休は除外
    out = [r for r in out if _norm_shift(r.get("shift", "")) != "公休"]
    # 日付昇順で整列
    out.sort(key=lambda x: x["date"]) 
    return out


def find_overlaps(
    my_slots: List[Dict[str, Any]],
    all_shifts: List[Dict[str, Any]],
    targets: List[str],
) -> List[Dict[str, Any]]:
    """同一勤務帯の一致を検出する。

    引数:
        my_slots: 自分のシフト一覧（{"date": "YYYY-MM-DD", "shift": "日勤"} の配列）
        all_shifts: 全員分のシフト（{"name": "氏名", "date": "YYYY-MM-DD", "shift": "日勤"} の配列）
        targets: 照合対象の氏名一覧

    戻り値:
        [{"date": 日付, "shift": 勤務, "with": [一致した氏名...]}] を日付昇順で返す。
    """
    my_map: Dict[str, str] = {}
    for slot in my_slots or []:
        d = str(slot.get("date", "")).strip()
        sh = _norm_shift(slot.get("shift", ""))
        if not d or not sh or sh == "公休":
            continue
        my_map[d] = sh

    target_set = {_norm_name(t) for t in (targets or []) if _norm_name(t)}
    if not target_set or not my_map:
        return []

    grouped: Dict[tuple, set] = {}
    for row in all_shifts or []:
        name = _norm_name(row.get("name", ""))
        if name not in target_set:
            continue
        d = str(row.get("date", "")).strip()
        sh = _norm_shift(row.get("shift", ""))
        if not d or not sh or sh == "公休":
            continue
        my_sh = my_map.get(d)
        if my_sh and my_sh == sh:
            key = (d, sh)
            grouped.setdefault(key, set()).add(name)

    events: List[Dict[str, Any]] = []
    for (d, sh), names in grouped.items():
        events.append({"date": d, "shift": sh, "with": sorted(names)})
    events.sort(key=lambda x: x["date"])
    return events
