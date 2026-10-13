
import logging
import re
import time
import unicodedata

from google import genai
from config import Config
from app.database import create_lead

logger = logging.getLogger(__name__)


class AIServiceError(Exception):
    pass


class AIService:
    def __init__(self):
        self.api_key = Config.GEMINI_API_KEY
        self.client = None

        # Önce en yeni Gemini 3 Flash modelini dene.
        self.models = [
            "gemini-3.5-flash-lite",
            "gemini-3.7-flash",
            "gemini-3.6-flash",
        ]

        if not self.api_key:
            logger.error(
                "[AI][CLIENT_UNAVAILABLE] GEMINI_API_KEY tanımlı değil."
            )
            return

        try:
            self.client = genai.Client(api_key=self.api_key)
            logger.info("[AI][CLIENT_READY] Gemini istemcisi hazır.")
        except Exception:
            logger.exception("[AI][CLIENT_INIT_FAILED]")
            self.client = None

    # --------------------------------------------------
    # METİN NORMALİZASYONU
    # --------------------------------------------------

    def normalize_text(self, text):
        if not isinstance(text, str):
            return ""

        text = unicodedata.normalize("NFC", text)
        return text.replace("İ", "i").replace("I", "ı").lower()

    # --------------------------------------------------
    # YANIT ÜRETİMİ
    # --------------------------------------------------

    def yanit_uret(self, user_message, conversation_history=None):
        return self.get_response(user_message, conversation_history)

    def get_response(self, user_message, conversation_history=None):
        history = (
            conversation_history
            if isinstance(conversation_history, list)
            else []
        )

        if not isinstance(user_message, str) or not user_message.strip():
            raise AIServiceError("Kullanıcı mesajı boş veya geçersiz.")

        user_message = user_message.strip()

        # Geçmiş konuşmaları topla.
        history_lines = []
        previous_messages = []

        for item in history:
            if not isinstance(item, dict):
                continue

            content = item.get("content", item.get("mesaj", ""))

            if not isinstance(content, str) or not content.strip():
                continue

            content = content.strip()
            previous_messages.append(content)

            role = item.get("role", "")
            if role == "user":
                history_lines.append(f"KULLANICI: {content}")
            elif role == "assistant":
                history_lines.append(f"ASİSTAN: {content}")

        full_text = self.normalize_text(
            " ".join(previous_messages + [user_message])
        )

        # Kelime veya sayfa sayısı.
        has_quantity = bool(
            re.search(
                r"\b\d[\d.,]*\s*(kelime\w*|word\w*|sayfa\w*|page\w*)\b",
                full_text,
            )
        )

        quantity_ranges = [
            "1.000 kelimeden az",
            "1.000 - 5.000 kelime",
            "5.000 - 10.000 kelime",
            "10.000+ kelime",
        ]

        has_quantity = has_quantity or any(
            item in full_text for item in quantity_ranges
        )

        # Teslim tarihi.
        delivery_patterns = [
            r"\b\d+\s*gün\b",
            r"\b\d+\s*hafta\b",
            r"\byarın\b",
            r"\bbugün\b",
            r"\bhaftaya\b",
            r"\bbu hafta\b",
            r"\bgelecek hafta\b",
            r"\bcuma\b",
            r"\bcumartesi\b",
            r"\bpazar\b",
            r"\bpazartesi\b",
            r"\bsalı\b",
            r"\bçarşamba\b",
            r"\bperşembe\b",
        ]

        delivery_options = [
            "standart teslim",
            "hızlı teslim",
            "hizli teslim",
            "acil teslim",
        ]

        has_delivery_date = (
            any(re.search(pattern, full_text) for pattern in delivery_patterns)
            or any(option in full_text for option in delivery_options)
        )

        # Dil bilgileri.
        has_english = bool(
            re.search(r"\bingilizce\w*\b|\benglish\w*\b", full_text)
        )
        has_turkish = bool(
            re.search(r"\btürkçe\w*\b|\bturkish\w*\b", full_text)
        )
        has_source_target = has_english and has_turkish

        # Metin türü.
        text_types = [
            "akademik",
            "hukuki",
            "teknik",
            "edebi",
            "edebî",
            "ticari",
            "makale",
            "tez",
            "belge",
            "doküman",
            "döküman",
            "academic",
            "article",
            "paper",
        ]

        has_text_type = any(item in full_text for item in text_types)

        # Bilgiler tamamlandıysa teklif bölümüne yönlendir.
        if (
            has_source_target
            and has_text_type
            and has_quantity
            and has_delivery_date
        ):
            return (
                "Harika! Çeviri yönünü, metin türünü, uzunluğunu ve "
                "teslim süresini aldım. Size özel teklif almak için "
                '"Teklif Al" bölümünden iletişim bilgilerinizi bırakabilirsiniz.'
            )

        # Dil, metin türü ve uzunluk var; teslim tarihi eksik.
        if (
            has_source_target
            and has_text_type
            and has_quantity
            and not has_delivery_date
        ):
            return (
                "Çeviri yönünü, metin türünü ve uzunluğunu aldım. "
                "Çevirinin teslim edilmesini istediğiniz tarih nedir?"
            )

        # Dil ve metin türü var; uzunluk eksik.
        if (
            has_source_target
            and has_text_type
            and not has_quantity
        ):
            return (
                "İngilizce → Türkçe çeviri talebinizi aldım. "
                "Metniniz yaklaşık kaç kelime veya kaç sayfa?"
            )

        # Dil ve uzunluk var; metin türü eksik.
        if (
            has_source_target
            and has_quantity
            and not has_text_type
        ):
            return (
                "İngilizce → Türkçe çeviri talebinizi ve metin uzunluğunu "
                "not aldım. Metninizin türü nedir?"
            )

        # Metin türü ve uzunluk var; dil bilgisi eksik.
        if (
            has_text_type
            and has_quantity
            and not has_source_target
        ):
            return (
                "Metninizin türünü ve uzunluğunu not aldım. "
                "Hangi dilden hangi dile çevrilmesini istiyorsunuz?"
            )

        # Gemini istemcisi yoksa sabit karşılama mesajı döndürme.
        if not self.client:
            raise AIServiceError(
                "Gemini istemcisi hazır değil. Render ortamında "
                "GEMINI_API_KEY ayarını kontrol edin."
            )

        # --------------------------------------------------
        # PROMPT
        # --------------------------------------------------

        prompt_parts = [
            str(getattr(Config, "BUSINESS_CONTEXT", "") or ""),
            """
Sen Transilation'ın Akıllı Satış Asistanısın.

Görevin, kullanıcının çeviri ihtiyacını anlamak ve teklif
sürecine yardımcı olmaktır.

Kurallar:
- Türkçe, doğal, nazik ve profesyonel konuş.
- Kullanıcının SON mesajına doğrudan cevap ver.
- Önceki mesajlarda verilen bilgileri tekrar sorma.
- Kaynak dili, hedef dili, metin türünü, uzunluğu ve teslim
  tarihini konuşma boyunca takip et.
- Kullanıcı birden fazla bilgi verdiyse hepsini dikkate al.
- Eksik olan en önemli bilgiyi sor; mümkünse tek soru sor.
- Kullanıcı selam verirse doğal bir selamla karşılık ver.
- Fiyat sorulursa doğrulanmamış fiyat uydurma.
- Bilgiler tamamlandığında kullanıcıyı "Teklif Al" bölümüne yönlendir.
- Kısa, açık ve doğal yanıtlar ver.
""",
        ]

        if history_lines:
            prompt_parts.append(
                "ÖNCEKİ KONUŞMA:\n" + "\n".join(history_lines)
            )

        prompt_parts.append(
            f"KULLANICININ SON MESAJI:\n{user_message}\n\n"
            "Önceki bilgileri tekrar sorma. Son mesaja uygun cevap ver."
        )

        prompt = "\n\n".join(prompt_parts)

        # --------------------------------------------------
        # GEMINI 3 MODELLERİ
        # --------------------------------------------------

        last_error = None

        for model_name in self.models:
            for attempt in range(2):
                try:
                    logger.info(
                        "[AI][REQUEST] model=%s attempt=%s",
                        model_name,
                        attempt + 1,
                    )

                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                    )

                    answer = (
                        response.text.strip()
                        if response and response.text
                        else ""
                    )

                    if not answer:
                        raise AIServiceError(
                            f"{model_name} boş yanıt döndürdü."
                        )

                    logger.info(
                        "[AI][SUCCESS] model=%s response_length=%s",
                        model_name,
                        len(answer),
                    )

                    return answer

                except AIServiceError:
                    raise

                except Exception as error:
                    last_error = error
                    error_text = str(error).lower()

                    temporary_error = any(
                        marker in error_text
                        for marker in [
                            "503",
                            "unavailable",
                            "high demand",
                            "429",
                            "resource_exhausted",
                            "404",
                            "not_found",
                            "not found",
                        ]
                    )

                    logger.warning(
                        "[AI][MODEL_FAILED] model=%s attempt=%s "
                        "temporary_or_model_error=%s error=%s",
                        model_name,
                        attempt + 1,
                        temporary_error,
                        str(error),
                    )

                    # Yetkilendirme veya başka kalıcı hatalarda
                    # diğer modelleri denemek sorunu çözmez.
                    if any(
                        marker in error_text
                        for marker in [
                            "401",
                            "403",
                            "unauthorized",
                            "permission_denied",
                            "invalid api key",
                        ]
                    ):
                        raise AIServiceError(
                            f"Gemini API erişim hatası: {error}"
                        ) from error

                    if attempt == 0:
                        time.sleep(2)

                    # İkinci başarısız denemede sıradaki modeli dene.
                    else:
                        break

        logger.error(
            "[AI][ALL_MODELS_FAILED] Son hata: %s",
            str(last_error),
        )

        raise AIServiceError(
            "Gemini 3 modellerinin hiçbiri yanıt üretemedi. "
            f"Son hata: {last_error}"
        ) from last_error

    # --------------------------------------------------
    # İSTEĞE BAĞLI FALLBACK
    # Gemini hatalarında otomatik kullanılmaz.
    # --------------------------------------------------

    def context_fallback(self, user_message, conversation_history=None):
        text = self.normalize_text(user_message)

        if any(
            word in text
            for word in ["çeviri", "çevir", "translate", "translation"]
        ):
            return (
                "Tabii, çeviri ihtiyacınızı birlikte belirleyelim. "
                "Hangi dilden hangi dile çeviri yapmak istiyorsunuz?"
            )

        return (
            "Mesajınızı aldım. Size doğru yardımcı olabilmem için "
            "nasıl bir çeviri hizmetine ihtiyacınız olduğunu anlatabilir misiniz?"
        )

    def fallback_response(self, user_message, conversation_history=None):
        return self.context_fallback(user_message, conversation_history)

    # --------------------------------------------------
    # LEAD KAYDI
    # --------------------------------------------------

    def save_lead(self, name, phone, message):
        if not name or not phone:
            return None

        return create_lead(
            name=name,
            phone=phone,
            message=message,
        )


ai_service = AIService()
