import re
import unicodedata

from google import genai

from config import Config
from app.database import create_lead


class AIServiceError(Exception):
    pass


class AIService:
    def __init__(self):
        self.api_key = Config.GEMINI_API_KEY
        self.client = None

        if self.api_key:
            try:
                self.client = genai.Client(
                    api_key=self.api_key
                )
            except Exception as error:
                print(
                    f"Gemini client initialization error: "
                    f"{type(error).__name__}: {error}",
                    flush=True
                )
                self.client = None

    def normalize_text(self, text):
        if not isinstance(text, str):
            return ""

        text = text.replace("İ", "i")
        text = text.replace("I", "ı")
        text = unicodedata.normalize("NFC", text)

        return text.lower()

    def yanit_uret(self, user_message, conversation_history=None):
        return self.get_response(
            user_message,
            conversation_history
        )

    def get_response(self, user_message, conversation_history=None):
        conversation_history = conversation_history or []

        if not isinstance(user_message, str):
            raise AIServiceError("Geçersiz kullanıcı mesajı.")

        user_message = user_message.strip()

        if not user_message:
            raise AIServiceError("Kullanıcı mesajı boş.")

        previous_messages = []

        for item in conversation_history:
            if not isinstance(item, dict):
                continue

            content = item.get("content", "")

            if isinstance(content, str) and content.strip():
                previous_messages.append(content.strip())

        previous_messages.append(user_message)

        full_text = self.normalize_text(
            " ".join(previous_messages)
        )

        # --------------------------------------------------
        # KELİME / SAYFA BİLGİSİ
        # --------------------------------------------------

        has_quantity = bool(
            re.search(
                r"\b\d[\d.,]*\s*(kelime\w*|word\w*|sayfa\w*|page\w*)\b",
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
            quantity in full_text
            for quantity in quantity_ranges
        )

        # --------------------------------------------------
        # TESLİM TARİHİ
        # --------------------------------------------------

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

        has_delivery_date = any(
            re.search(pattern, full_text)
            for pattern in delivery_patterns
        ) or any(
            option in full_text
            for option in delivery_options
        )

        # --------------------------------------------------
        # KAYNAK DİL
        # --------------------------------------------------

        has_english = bool(
            re.search(
                r"\bingilizce\w*\b|\benglish\w*\b",
                full_text
            )
        )

        # --------------------------------------------------
        # HEDEF DİL
        # --------------------------------------------------

        has_turkish = bool(
            re.search(
                r"\btürkçe\w*\b|\bturkish\w*\b",
                full_text
            )
        )

        has_source_target = (
            has_english
            and has_turkish
        )

        # --------------------------------------------------
        # METİN TÜRÜ
        # --------------------------------------------------

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

        has_text_type = any(
            word in full_text
            for word in text_types
        )

        # --------------------------------------------------
        # BÜTÜN BİLGİLER TAMAM
        # --------------------------------------------------

        if (
            has_source_target
            and has_text_type
            and has_quantity
            and has_delivery_date
        ):
            return (
                "Harika! Çeviri yönü, metin türü, metin uzunluğu "
                "ve teslim süresini aldım. Size özel teklif almak "
                'için "Teklif Al" bölümünden iletişim bilgilerinizi '
                "bırakabilirsiniz."
            )

        # --------------------------------------------------
        # DİL + AKADEMİK VAR, UZUNLUK YOK
        # --------------------------------------------------

        if (
            has_source_target
            and has_text_type
            and not has_quantity
        ):
            return (
                "Harika! İngilizce → Türkçe akademik çeviri için "
                "metniniz yaklaşık kaç kelime veya kaç sayfa?"
            )

        # --------------------------------------------------
        # DİL + AKADEMİK + UZUNLUK VAR
        # TESLİM TARİHİ YOK
        # --------------------------------------------------

        if (
            has_source_target
            and has_text_type
            and has_quantity
            and not has_delivery_date
        ):
            return (
                "Harika! İngilizce → Türkçe akademik çeviri "
                "talebinizi ve metin uzunluğunu aldım. "
                "Çevirinin teslim edilmesini istediğiniz tarih nedir?"
            )

        # --------------------------------------------------
        # DİL + UZUNLUK VAR, METİN TÜRÜ YOK
        # --------------------------------------------------

        if (
            has_source_target
            and has_quantity
            and not has_text_type
        ):
            return (
                "Anladım. İngilizce → Türkçe çeviri talebinizi "
                "ve metin uzunluğunu not aldım. Metnin türü nedir?"
            )

        # --------------------------------------------------
        # METİN TÜRÜ + UZUNLUK VAR, DİL YOK
        # --------------------------------------------------

        if (
            has_text_type
            and has_quantity
            and not has_source_target
        ):
            return (
                "Anladım. Metninizin yaklaşık uzunluğunu ve "
                "türünü not aldım. Çeviri hangi dilden hangi "
                "dile yapılacak?"
            )

        # --------------------------------------------------
        # GEMINI YOKSA FALLBACK
        # --------------------------------------------------

        if not self.client:
            return self.context_fallback(
                user_message,
                conversation_history
            )

        # --------------------------------------------------
        # GEMINI PROMPT
        # --------------------------------------------------

        prompt = Config.BUSINESS_CONTEXT + """

Sen Transilation'ın Akıllı Satış Asistanısın.

Görevin kullanıcının çeviri ihtiyacını anlamasına ve teklif
sürecine yönlendirilmesine yardımcı olmaktır.

Kurallar:

1. Türkçe, doğal, kısa ve profesyonel konuş.
2. Önceki mesajlarda verilen bilgileri hatırla.
3. Daha önce verilen bilgileri tekrar sorma.
4. Kaynak dil, hedef dil, metin türü, kelime/sayfa sayısı
   ve teslim tarihini takip et.
5. Kullanıcı aynı mesajda birden fazla bilgi verdiyse
   hepsini dikkate al.
6. Gereksiz soru sorma.
7. Mümkünse yalnızca bir soru sor.
8. Fiyat sorulursa kesin veya uydurma fiyat verme.
9. Gerekli bilgiler tamamlandığında kullanıcıyı
   "Teklif Al" bölümüne yönlendir.
10. Kısa cevaplar ver.
"""

        if conversation_history:
            prompt += "\n--- KONUŞMA GEÇMİŞİ ---\n"

            for item in conversation_history:
                if not isinstance(item, dict):
                    continue

                role = item.get("role", "")
                content = item.get("content", "")

                if not isinstance(content, str):
                    continue

                content = content.strip()

                if not content:
                    continue

                if role == "user":
                    prompt += f"KULLANICI: {content}\n"

                elif role == "assistant":
                    prompt += f"ASİSTAN: {content}\n"

            prompt += "\n--- KONUŞMA GEÇMİŞİ SONU ---\n"

        prompt += f"""

KULLANICININ SON MESAJI:

{user_message}

Önceki konuşmada verilmiş bilgileri tekrar sorma.

Eksik olan en önemli bilgiyi belirle.

Mümkünse yalnızca bir soru sor.

Kısa ve doğal Türkçe cevap ver.
"""

        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )

            if response and response.text:
                return response.text.strip()

            return self.context_fallback(
                user_message,
                conversation_history
            )

        except Exception as error:
            print(
                f"Gemini API Error: "
                f"{type(error).__name__}: {error}",
                flush=True
            )

            return self.context_fallback(
                user_message,
                conversation_history
            )

    # ------------------------------------------------------
    # FALLBACK
    # ------------------------------------------------------

    def context_fallback(
        self,
        user_message,
        conversation_history=None
    ):
        history = conversation_history or []

        combined_parts = []

        for item in history:
            if not isinstance(item, dict):
                continue

            content = item.get("content", "")

            if isinstance(content, str) and content.strip():
                combined_parts.append(content.strip())

        combined_parts.append(user_message)

        text = self.normalize_text(
            " ".join(combined_parts)
        )

        # Kelime / sayfa
        has_quantity = bool(
            re.search(
                r"\b\d[\d.,]*\s*(kelime\w*|word\w*|sayfa\w*|page\w*)\b",
                text
            )
        )

        has_quantity = has_quantity or any(
            quantity in text
            for quantity in [
                "1.000 kelimeden az",
                "1.000 - 5.000 kelime",
                "5.000 - 10.000 kelime",
                "10.000+ kelime",
            ]
        )

        # Diller
        has_english = bool(
            re.search(
                r"\bingilizce\w*\b|\benglish\w*\b",
                text
            )
        )

        has_turkish = bool(
            re.search(
                r"\btürkçe\w*\b|\bturkish\w*\b",
                text
            )
        )

        # Çeviri
        has_translation = any(
            word in text
            for word in [
                "çeviri",
                "çevir",
                "çevirmek",
                "translate",
                "translation",
            ]
        )

        # Akademik
        has_academic = any(
            word in text
            for word in [
                "akademik",
                "makale",
                "tez",
                "academic",
                "article",
                "paper",
            ]
        )

        # --------------------------------------------------
        # İNGİLİZCE → TÜRKÇE + AKADEMİK + UZUNLUK
        # --------------------------------------------------

        if (
            has_english
            and has_turkish
            and has_academic
            and has_quantity
        ):
            return (
                "Harika! İngilizce → Türkçe akademik "
                "çeviri talebinizi ve metin uzunluğunu aldım. "
                "Çevirinin teslim edilmesini istediğiniz tarih nedir?"
            )

        # --------------------------------------------------
        # İNGİLİZCE → TÜRKÇE + AKADEMİK
        # --------------------------------------------------

        if (
            has_english
            and has_turkish
            and has_academic
        ):
            return (
                "Harika! İngilizce → Türkçe akademik "
                "çeviri talebinizi aldım. Metniniz "
                "yaklaşık kaç kelime veya kaç sayfa?"
            )

        # --------------------------------------------------
        # İNGİLİZCE → TÜRKÇE + UZUNLUK
        # --------------------------------------------------

        if (
            has_english
            and has_turkish
            and has_quantity
        ):
            return (
                "Anladım. İngilizce → Türkçe çeviri "
                "talebinizi ve metin uzunluğunu not aldım. "
                "Metnin türü nedir?"
            )

        # --------------------------------------------------
        # ÇEVİRİ + UZUNLUK
        # --------------------------------------------------

        if (
            has_translation
            and has_quantity
        ):
            return (
                "Anladım. Çeviri metninizin uzunluğunu "
                "not aldım. Hangi dilden hangi dile "
                "çeviri yapılacak?"
            )

        # --------------------------------------------------
        # SADECE ÇEVİRİ
        # --------------------------------------------------

        if has_translation:
            return (
                "Tabii! Çeviri ihtiyacınızı belirleyelim. "
                "Hangi dilden hangi dile çeviri yapmak "
                "istiyorsunuz?"
            )

        # --------------------------------------------------
        # GENEL KARŞILAMA
        # --------------------------------------------------

        return (
            "Merhaba! 👋 Ben Transilation'ın Akıllı Satış "
            "Asistanıyım. Çeviri ihtiyacınızı belirlemenize "
            "ve teklif sürecine yardımcı olabilirim. "
            "Nasıl bir çeviriye ihtiyacınız var?"
        )

    def fallback_response(
        self,
        user_message,
        conversation_history=None
    ):
        return self.context_fallback(
            user_message,
            conversation_history
        )

    # ------------------------------------------------------
    # LEAD KAYDI
    # ------------------------------------------------------

    def save_lead(self, name, phone, message):
        if not name or not phone:
            return None

        return create_lead(
            name=name,
            phone=phone,
            message=message
        )


    def yanit_uret(self, user_message, conversation_history=None):
        return self.get_response(user_message, conversation_history)


ai_service = AIService()