import logging

from flask import (
    Blueprint,
    jsonify,
    render_template,
    request,
    Response,
)

from config import Config
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


def dashboard_auth_required():
    auth = request.authorization

    if not auth:
        return False

    username_ok = auth.username == Config.ADMIN_USERNAME
    password_ok = auth.password == Config.ADMIN_PASSWORD

    return username_ok and password_ok


@bp.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@bp.route("/assistant", methods=["GET"])
def assistant():
    return render_template("assistant.html")


@bp.route("/dashboard", methods=["GET"])
def dashboard():
    if not dashboard_auth_required():
        return unauthorized_response()

    leads = [
        _serialize_lead(lead)
        for lead in tum_leadler()
    ]

    return render_template(
        "dashboard.html",
        leads=leads
    )


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
        logger.error(
            "[CHAT][INVALID_JSON] Gelen veri geçerli JSON nesnesi değil."
        )
        return jsonify({
            "basari": False,
            "success": False,
            "hata": "Geçerli bir JSON nesnesi gönderilmedi.",
            "error": "A valid JSON object is required.",
        }), 400

    mesaj = data.get("mesaj") or data.get("message", "")
    gecmis = data.get("gecmis") or data.get("history", [])

    # Hassas içerikleri terminale basmadan mesajın geldiğini doğrula.
    logger.info(
        "[CHAT][INPUT] mesaj_tipi=%s mesaj_uzunlugu=%s "
        "gecmis_tipi=%s gecmis_adedi=%s",
        type(mesaj).__name__,
        len(mesaj) if isinstance(mesaj, str) else "gecersiz",
        type(gecmis).__name__,
        len(gecmis) if isinstance(gecmis, list) else "gecersiz",
    )

    if not isinstance(mesaj, str) or not mesaj.strip():
        logger.warning("[CHAT][VALIDATION] Boş veya geçersiz mesaj.")
        return jsonify({
            "basari": False,
            "success": False,
            "hata": "Mesaj boş gönderildi.",
            "error": "Message cannot be empty.",
        }), 400

    if not isinstance(gecmis, list):
        logger.warning("[CHAT][HISTORY] Geçersiz geçmiş; boş liste kullanılıyor.")
        gecmis = []

    try:
        cevap = ai_service.yanit_uret(
            mesaj.strip(),
            gecmis
        )

        logger.info(
            "[CHAT][RESPONSE] cevap_tipi=%s cevap_uzunlugu=%s",
            type(cevap).__name__,
            len(cevap) if isinstance(cevap, str) else "gecersiz",
        )

        if not isinstance(cevap, str) or not cevap.strip():
            logger.error("[CHAT][EMPTY_RESPONSE] AI boş yanıt üretti.")
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
            "hata": "İsim ve telefon gerekli",
            "error": "Name and phone are required",
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

    except Exception as error:
        logger.exception(
            "Database error in POST /api/leads"
        )

        return jsonify({
            "basari": False,
            "success": False,
            "hata": "Kayıt sırasında bir veritabanı hatası oluştu.",
            "error": "A database error occurred while saving the lead.",
            "detail": str(error),
        }), 500


@bp.route("/api/leads", methods=["GET"])
def get_leads():
    if not dashboard_auth_required():
        return unauthorized_response()

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

    except Exception as error:
        logger.exception(
            "Database error in GET /api/leads"
        )

        return jsonify({
            "basari": False,
            "success": False,
            "hata": "Kayıtlar çekilirken hata oluştu.",
            "error": "An error occurred while retrieving leads.",
            "detail": str(error),
        }), 500
