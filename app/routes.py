from flask import Blueprint, jsonify, render_template, request

from app.database import lead_ekle, tum_leadler
from services.ai_service import ai_service


bp = Blueprint("routes", __name__)


@bp.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@bp.route("/dashboard", methods=["GET"])
def dashboard():
    return render_template("dashboard.html")


@bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "Transilation Smart Sales Assistant"}), 200


@bp.route("/api/sohbet", methods=["POST"])
def sohbet():
    try:
        data = request.get_json(force=True, silent=True) or {}
        mesaj = data.get("mesaj") or data.get("message", "")
        gecmis = data.get("gecmis") or data.get("history", [])

        if not str(mesaj).strip():
            return jsonify({"basari": False, "hata": "Mesaj boş gönderildi"}), 400

        cevap = ai_service.yanit_uret(mesaj, gecmis)
        return jsonify({"basari": True, "cevap": cevap}), 200
    except Exception:
        return jsonify({"basari": False, "hata": "Sunucu tarafında beklenmeyen bir hata oluştu."}), 500


@bp.route("/api/leads", methods=["POST"])
def leads():
    try:
        data = request.get_json(force=True, silent=True) or {}
        isim = data.get("isim") or data.get("name", "")
        telefon = data.get("telefon") or data.get("phone", "")
        mesaj = data.get("mesaj") or data.get("message", "")

        if not isim or not telefon:
            return jsonify({"basari": False, "hata": "İsim ve telefon gerekli"}), 400

        lead_id = lead_ekle(isim, telefon, mesaj)
        return jsonify({"basari": True, "id": lead_id}), 201
    except Exception:
        return jsonify({"basari": False, "hata": "Kayıt sırasında bir veritabanı hatası oluştu."}), 500


@bp.route("/api/leads", methods=["GET"])
def get_leads():
    try:
        leads_list = [
            {
                "id": lead["id"],
                "isim": lead["isim"],
                "telefon": lead["telefon"],
                "mesaj": lead["mesaj"],
                "tarih": lead["tarih"],
            }
            for lead in tum_leadler()
        ]
        return jsonify({"basari": True, "leads": leads_list}), 200
    except Exception:
        return jsonify({"basari": False, "hata": "Kayıtlar çekilirken hata oluştu."}), 500