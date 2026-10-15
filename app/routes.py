
import logging

from flask import (
    Blueprint,
    jsonify,
    render_template,
    request,
)

from app.database import lead_ekle, tum_leadler
from app.services.ai_service import AIServiceError, ai_service


logger = logging.getLogger(__name__)

bp = Blueprint("routes", __name__)


def _serialize_lead(lead):
    return {
        "id": lead["id"],
        "isim": lead["isim"],
        "telefon": lead["telefon"],
        "mesaj": lead["mesaj"],
        "tarih": lead["tarih"],
        "name": lead["isim"],
        "phone": lead["telefon"],
        "message": lead["mesaj"],
        "created_at": lead["tarih"],
    }


@bp.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@bp.route("/assistant", methods=["GET"])
def assistant():
    return render_template("assistant.html")


@bp.route("/dashboard", methods=["GET"])
def dashboard():
    try:
        leads = [
            _serialize_lead(lead)
            for lead in tum_leadler()
        ]

        return render_template(
            "dashboard.html",
            leads=leads
        )

    except Exception:
        logger.exception("Error handling GET /dashboard")
        return "Yönetim paneli yüklenirken hata oluştu.", 500


@bp.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "Transilation Smart Sales Assistant",
        "durum": "canli",
    }), 200


@bp.route("/api/sohbet", methods=["POST"])
def sohbet():
    data = request.get_json(silent=True)

    logger.info(
        "[CHAT][REQUEST] method=%s path=%s content_type=%s",
        request.method,
        request.path,
        request.content_type,
    )

    if not isinstance(data, dict):
        return jsonify({
            "basari": False,
            "success": False,
            "hata": "Geçerli bir JSON nesnesi gönderilmedi.",
            "error": "A valid JSON object is required.",
        }), 400

    mesaj = data.get("mesaj") or data.get("message", "")
    gecmis = data.get("gecmis") or data.get("history", [])

    if not isinstance(mesaj, str) or not mesaj.strip():
        return jsonify({
            "basari": False,
            "success": False,
            "hata": "Mesaj boş gönderildi.",
            "error": "Message cannot be empty.",
        }), 400

    if not isinstance(gecmis, list):
        gecmis = []

    try:
        cevap = ai_service.yanit_uret(
            mesaj.strip(),
            gecmis
        )

        if not isinstance(cevap, str) or not cevap.strip():
            return jsonify({
                "basari": False,
                "success": False,
                "hata": "Asistan boş yanıt üretti.",
                "error": "Assistant returned an empty response.",
            }), 502

        return jsonify({
            "basari": True,
            "success": True,
            "cevap": cevap,
            "response": cevap,
        }), 200

    except AIServiceError as error:
        logger.exception("[CHAT][AI_SERVICE_ERROR]")

        return jsonify({
            "basari": False,
            "success": False,
            "hata": "Yapay zekâ servisi yanıt üretemedi.",
            "error": str(error),
        }), 503

    except Exception:
        logger.exception("[CHAT][UNEXPECTED_ERROR]")

        return jsonify({
            "basari": False,
            "success": False,
            "hata": "Sunucu tarafında beklenmeyen hata oluştu.",
            "error": "Unexpected server error.",
        }), 500


@bp.route("/api/leads", methods=["POST"])
def create_lead():
    data = request.get_json(silent=True) or {}

    isim = data.get("isim") or data.get("name", "")
    telefon = data.get("telefon") or data.get("phone", "")
    mesaj = data.get("mesaj") or data.get("message", "")

    if (
        not isinstance(isim, str)
        or not isim.strip()
        or not isinstance(telefon, str)
        or not telefon.strip()
    ):
        return jsonify({
            "basari": False,
            "success": False,
            "hata": "İsim ve telefon gerekli.",
            "error": "Name and phone are required.",
        }), 400

    try:
        lead_id = lead_ekle(
            isim.strip(),
            telefon.strip(),
            str(mesaj)
        )

        return jsonify({
            "basari": True,
            "success": True,
            "id": lead_id,
            "lead_id": lead_id,
            "mesaj": "Müşteri adayı başarıyla kaydedildi.",
            "message": "Lead saved successfully.",
        }), 201

    except Exception:
        logger.exception("Database error in POST /api/leads")

        return jsonify({
            "basari": False,
            "success": False,
            "hata": "Kayıt sırasında bir veritabanı hatası oluştu.",
            "error": "A database error occurred while saving the lead.",
        }), 500


@bp.route("/api/leads", methods=["GET"])
def get_leads():
    try:
        leads = [
            _serialize_lead(lead)
            for lead in tum_leadler()
        ]

        return jsonify({
            "basari": True,
            "success": True,
            "leads": leads,
            "data": leads,
        }), 200

    except Exception:
        logger.exception("Database error in GET /api/leads")

        return jsonify({
            "basari": False,
            "success": False,
            "hata": "Kayıtlar çekilirken hata oluştu.",
            "error": "An error occurred while retrieving leads.",
        }), 500
