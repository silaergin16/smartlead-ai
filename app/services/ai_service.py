
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
        self.model = getattr(
            Config,
            "GEMINI_MODEL",
            "gemini-2.5-flash"
        )

        if not self.api_key:
            logger.error(
                "[AI][CLIENT_UNAVAILABLE] GEMINI_API_KEY tanımlı değil."
            )
            return

        try:
            self.client = genai.Client(api_key=self.api_key)
            logger.info(
                "[AI][CLIENT_READY] Gemini istemcisi hazır. model=%s",
                self.model
            )
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
    # ANA YANIT FONKSİYONU
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

        # Geçmiş konuşmaları birleştir.
        previous_messages = []

        for item in history:
            if not isinstance(item, dict):
                continue

            content = item.get("content", item.get("mesaj", ""))

            if isinstance(content, str) and content.strip():
                previous_messages.append(content.strip())

        full_text = self.normalize_text(
            " ".join(previous_messages + [user_message])
        )

        # Kelime / sayfa sayısı
        has_quantity = bool(
            re.search(
                r"\b\d[\d.,]*\s*(?:kelime\w*|word\w*|sayfa\w*|page\w*)\b",
                full_text
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

        # Teslim tarihi
        delivery_patterns = [
            r"\b\d+\s*gün\b",
            r"\b\d+\s*hafta\b",
            r"\byarın\b",
            r"\bbugün\b",
            r"\bhaftaya\b",
            r"\bb u hafta\b",
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
            any(re.search(p, full_text) for p in delivery_patterns)
            or any(item in full_text for item in delivery_options)
        )

        # Diller
        has_english = bool(
            re.search(r"\bingilizce\w*\b|\benglish\w*\b", full_text)
        )
        has_turkish = bool(
            re.search(r"\btürkçe\w*\b|\bturkish\w*\b", full_text)
        )
        has_source_target = has_english and has_turkish

        # Metin türü
        text_types = [
            "akademik", "hukuki", "teknik", "edebi", "edebî",
            "ticari", "makale", "tez", "belge", "doküman",
            "döküman", "academic", "article", "paper",
        ]

        has_text_type = any(item in full_text for item in text_types)

        # Bilgiler tamamlandıysa sonraki adıma yönlendir.
        if (
            has_source_target
            and has_text_type
            and has_quantity
            and has_delivery_date
        ):
            return (
                "Harika! Çeviri yönünü, metin türünü, uzunluğunu "
                "ve teslim süresini aldım. Size özel teklif için "
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
                "İngilizce → Türkçe çeviri talebinizi ve uzunluğu "
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

        # Gemini kullanılamıyorsa gerçek hatayı gizleme.
        if not self.client:
            raise AIServiceError(
                "Gemini istemcisi hazır değil. Render ortamında "
                "GEMINI_API_KEY ayarını ve başlangıç loglarını kontrol edin."
            )

        # --------------------------------------------------
        # GEMINI PROMPT
        # --------------------------------------------------

        prompt_parts = [
            str(getattr(Config, "BUSINESS_CONTEXT", "") or ""),
            """
Sen Transilation'ın Akıllı Satış Asistanısın.

Görevin müşterinin çeviri ihtiyacını anlamak ve teklif sürecine
yardımcı olmaktır.

Kurallar:
- Türkçe, doğal, nazik ve profesyonel konuş.
- Kullanıcının son mesajına doğrudan cevap ver.
- Önceki mesajlarda verilmiş bilgileri tekrar sorma.
- Kaynak dili, hedef dili, metin türünü, uzunluğu ve teslim
  tarihini konuşma boyunca takip et.
- Birden fazla bilgi verilmişse hepsini dikkate al.
- Eksik olan en önemli bilgiyi sor; mümkünse tek soru sor.
- Kullanıcı yalnızca selam verirse selamını doğal biçimde karşıla.
- Fiyat sorulursa doğrulanmamış fiyat uydurma.
- Bilgiler tamamlandığında kullanıcıyı "Teklif Al" bölümüne yönlendir.
- Kısa, açık ve doğal yanıtlar ver.
""",
        ]

        if history:
            history_lines = []

            for item in history:
                if not isinstance(item, dict):
                    continue

                role = item.get("role", "")
                content = item.get("content", item.get("mesaj", ""))

                if not isinstance(content, str) or not content.strip():
                    continue

                if role == "user":
                    history_lines.append(f"KULLANICI: {content.strip()}")
                elif role == "assistant":
                    history_lines.append(f"ASİSTAN: {content.strip()}")

            if history_lines:
                prompt_parts.append(
                    "ÖNCEKİ KONUŞMA:\n" + "\n".join(history_lines)
                )

        prompt_parts.append(
            f"KULLANICININ SON MESAJI:\n{user_message}\n\n"
            "Önceki bilgileri tekrar sorma. Son mesaja uygun yanıt ver."
        )

        prompt = "\n\n".join(prompt_parts)

        # --------------------------------------------------
        # GEMINI İSTEĞİ VE GEÇİCİ HATALARDA TEKRAR DENEME
        # --------------------------------------------------

        for attempt in range(3):
            try:
                logger.info(
                    "[AI][REQUEST] model=%s attempt=%s message_length=%s history_count=%s",
                    self.model,
                    attempt + 1,
                    len(user_message),
                    len(history),
                )

                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                )

                answer = (
                    response.text.strip()
                    if response and response.text
                    else ""
                )

                if not answer:
                    raise AIServiceError(
                        "Gemini boş yanıt döndürdü."
                    )

                logger.info(
                    "[AI][SUCCESS] model=%s response_length=%s",
                    self.model,
                    len(answer),
                )

                return answer

            except AIServiceError:
                raise

            except Exception as error:
                error_text = str(error).lower()
                transient = (
                    "503" in error_text
                    or "unavailable" in error_text
                    or "high demand" in error_text
                    or "429" in error_text
                    or "resource_exhausted" in error_text
                )

                if transient and attempt < 2:
                    wait_seconds = 2 ** (attempt + 1)

                    logger.warning(
                        "[AI][RETRY] attempt=%s wait_seconds=%s error=%s",
                        attempt + 1,
                        wait_seconds,
                        str(error),
                    )

                    time.sleep(wait_seconds)
                    continue

                logger.exception(
                    "[AI][REQUEST_FAILED] model=%s",
                    self.model,
                )

                raise AIServiceError(
                    f"Gemini yanıt üretemedi: {type(error).__name__}: {error}"
                ) from error

        raise AIServiceError(
            "Gemini üç denemeden sonra yanıt üretemedi."
        )

    # --------------------------------------------------
    # İSTEĞE BAĞLI FALLBACK
    # Gemini hatalarında otomatik olarak kullanılmaz.
    # --------------------------------------------------

    def context_fallback(self, user_message, conversation_history=None):
        text = self.normalize_text(user_message)

        if any(word in text for word in ["çeviri", "çevir", "translate", "translation"]):
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
