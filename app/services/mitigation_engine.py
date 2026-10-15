"""Rule-based mitigation engine.

Pipeline: INPUT DATA -> MODEL PREDICTION -> RISK SCORE -> SHAP FACTORS
-> RULE ENGINE -> FINAL RECOMMENDATION.

Deterministic: same (level, factors) always yields same decision.
No randomness, no ML retraining. XGBoost/SHAP stay the predictors;
this module only translates their output into auditable actions.
"""

from __future__ import annotations


def _canon(name: str) -> str:
    n = (name or "").lower()
    if "effective" in n and "drain" in n or "kapasitas drainase" in n:
        return "effective_drainage_capacity"
    if "drainase" in n or ("drain" in n and "effective" not in n):
        return "drainage_density"
    if "population" in n or "penduduk" in n or "demograf" in n:
        return "population_density"
    if "rainfall" in n or "hujan" in n or "presipitasi" in n or "curah" in n:
        return "rainfall"
    if "elevation" in n or "elevasi" in n or "mdpl" in n:
        return "elevation"
    if "slope" in n or "lereng" in n:
        return "slope"
    if "basin" in n or "cekungan" in n or "depresi" in n:
        return "basin"
    if "river" in n or "sungai" in n:
        return "river"
    if "road" in n or "jalan" in n:
        return "road"
    if "building" in n or "bangunan" in n:
        return "building"
    if "impervious" in n or "kedap" in n:
        return "impervious"
    if "green" in n or "hijau" in n or "resapan" in n or "infiltrat" in n:
        return "green"
    if "water" in n and "ratio" in n or "badan air" in n:
        return "water"
    if "facility" in n or "fasilitas" in n:
        return "facility"
    return "other"


def _pct(f: dict) -> float:
    try:
        return float(f.get("contribution", 0) or 0)
    except (TypeError, ValueError):
        return 0.0


def build_decision(
    district_id: str,
    district: str,
    score: int,
    level: str,
    confidence: int,
    factors: list[dict],
) -> dict:
    """Build evidence-backed mitigation decision from SHAP-ranked factors."""
    level = (level or "low").lower()
    ranked = sorted(factors or [], key=_pct, reverse=True)
    by_key: dict[str, dict] = {}
    for f in ranked:
        by_key.setdefault(_canon(str(f.get("factor", ""))), f)

    def contrib(key: str) -> float:
        return _pct(by_key.get(key, {}))

    top = ranked[:2]
    why = []
    for f in top:
        fname = str(f.get("factor", ""))
        c = _pct(f)
        key = _canon(fname)
        reason = {
            "effective_drainage_capacity": f"Kapasitas drainase menjadi faktor terbesar ({c:g}%) — aliran air terhambat saat hujan ekstrem.",
            "drainage_density": f"Kerapatan drainase berkontribusi {c:g}% — jaringan saluran tidak memadai untuk volume limpasan.",
            "population_density": f"Kepadatan penduduk berkontribusi {c:g}% — potensi dampak terhadap jiwa tinggi.",
            "rainfall": f"Intensitas hujan berkontribusi {c:g}% — beban hidrologi melebihi kapasitas tampung.",
            "elevation": f"Elevasi rendah berkontribusi {c:g}% — wilayah cekungan menampung genangan.",
            "slope": f"Kelerengan datar berkontribusi {c:g}% — aliran lambat, air menggenang.",
            "basin": f"Indeks depresi cekungan berkontribusi {c:g}% — topografi menahan air.",
            "river": f"Kerapatan sungai berkontribusi {c:g}% — luapan badan air saat debit puncak.",
            "road": f"Kerapatan jalan berkontribusi {c:g}% — permukaan kedap mempercepat limpasan.",
            "building": f"Kepadatan bangunan berkontribusi {c:g}% — area terbangun mengurangi resapan.",
            "impervious": f"Rasio kedap air berkontribusi {c:g}% — limpasan permukaan dominan.",
            "green": f"Minimnya area hijau berkontribusi {c:g}% — resapan alami tidak mencukupi.",
            "water": f"Rasio badan air berkontribusi {c:g}% — kapasitas tampung perairan terbatas.",
            "facility": f"Kepadatan fasilitas kritis berkontribusi {c:g}% — aset vital terpapar risiko.",
        }.get(key, f"{fname} berkontribusi {c:g}% terhadap skor risiko.")
        why.append({"factor": fname, "contribution": c, "reason": reason})

    actions: list[dict] = []
    seen: set[str] = set()

    def add(title: str, priority: str, reason: str):
        if title not in seen:
            seen.add(title)
            actions.append({"title": title, "priority": priority, "reason": reason})

    if contrib("effective_drainage_capacity") >= 30:
        c = contrib("effective_drainage_capacity")
        add("Normalisasi drainase utama", "High",
            f"Kapasitas drainase merupakan faktor risiko dominan ({c:g}%).")
    if contrib("drainage_density") >= 25:
        c = contrib("drainage_density")
        add("Pembersihan sedimentasi saluran", "High" if level == "high" else "Medium",
            f"Kerapatan drainase berkontribusi {c:g}% — sumbatan memperparah genangan.")
    if contrib("population_density") >= 20 and level == "high":
        c = contrib("population_density")
        add("Kesiapsiagaan evakuasi + early warning", "High",
            f"Kepadatan penduduk ({c:g}%) pada risiko tinggi — prioritaskan keselamatan jiwa.")
    if contrib("rainfall") >= 25 or contrib("river") >= 20:
        c = max(contrib("rainfall"), contrib("river"))
        add("Pemantauan debit & status siaga pompa", "Medium",
            f"Beban hidrologi berkontribusi {c:g}% — siagakan pompa dan posko saat hujan ekstrem.")
    if contrib("elevation") >= 15 or contrib("basin") >= 15 or contrib("slope") >= 15:
        dom = max((contrib("elevation"), "elevasi"), (contrib("basin"), "cekungan"), (contrib("slope"), "kelerengan"), key=lambda x: x[0])
        add("Infrastruktur pengendali banjir", "Medium",
            f"Kondisi {dom[1]} berkontribusi {dom[0]:g}% — butuh tanggul/kolam retensi.")
    if contrib("impervious") >= 15 or contrib("green") >= 15:
        add("Optimalisasi area resapan", "Medium",
            "Minimnya resapan memperbesar limpasan — tambah sumur resapan dan ruang hijau.")
    if contrib("road") >= 20 or contrib("building") >= 20 or contrib("facility") >= 20:
        add("Proteksi infrastruktur & fasilitas kritis", "Medium" if level == "high" else "Low",
            "Aset terbangun padat terpapar — amankan akses dan fasilitas vital.")
    if level == "high" and not any(a["priority"] == "High" for a in actions):
        add("Perkuatan tanggul saluran kritis", "High",
            "Risiko tinggi tanpa faktor dominan tunggal — amankan titik paling rentan.")
    if level == "medium" and not actions:
        add("Pemeliharaan drainase berkala", "Medium",
            "Risiko sedang — cegah eskalasi via desiltasi rutin.")
    add("Monitoring area rawan genangan", "Low",
        "Pemantauan berkala untuk deteksi dini perubahan risiko.")

    prio_order = {"High": 0, "Medium": 1, "Low": 2}
    actions.sort(key=lambda a: prio_order.get(a["priority"], 3))

    headline = actions[0]["title"] if actions else "Pemantauan rutin"
    return {
        "districtId": district_id,
        "district": district,
        "risk_summary": {
            "districtId": district_id,
            "district": district,
            "score": score,
            "level": level,
            "confidence": confidence,
        },
        "why_this_action": why,
        "supporting_data": [
            {"factor": str(f.get("factor", "")), "value": str(f.get("value", "—")), "contribution": _pct(f)}
            for f in ranked
        ],
        "actions": actions,
        "headline_action": headline,
    }
