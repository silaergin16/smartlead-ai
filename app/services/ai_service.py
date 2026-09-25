import re

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
            self.client = genai.Client(
                api_key=self.api_key
            )

    def get_response(self, user_message, conversation_history=None):

        conversation_history = conversation_history or []

        # Tüm konuşmayı birleştir
        all_text = []

        for item in conversation_history:
            content = item.get("content", "").strip()

            if content:
                all_text.append(content)

        all_text.append(user_message)

        full_text = " ".join(all_text).lower()

        # ---------------------------------------------
        # KELİME / SAYFA SAYISI
        # ---------------------------------------------

        has_quantity = bool(
            re.search(
                r"\b\d+\s*(kelime|word|sayfa)\b",
                full_text
            )
        )

        # ---------------------------------------------
        # TESLİM TARİHİ
        # ---------------------------------------------

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

        has_delivery_date = any(
            re.search(pattern, full_text)
            for pattern in delivery_patterns
        )

        # ---------------------------------------------
        # KAYNAK + HEDEF DİL
        # ---------------------------------------------

        has_source_target = (
            "ingilizce" in full_text
            and "türkçe" in full_text
        )

        # ---------------------------------------------
        # METİN TÜRÜ
        # ---------------------------------------------

        text_types = [
            "akademik",
            "hukuki",
            "teknik",
            "edebi",
            "ticari",
            "makale",
            "tez",
            "belge"
        ]

        has_text_type = any(
            word in full_text
            for word in text_types
        )

        # ---------------------------------------------
        # 1. AŞAMA
        # Dil + metin türü var
        # Kelime sayısı yok
        # ---------------------------------------------

        if (
            has_source_target
            and has_text_type
            and not has_quantity
        ):
            return (
                "Harika! İngilizce → Türkçe akademik "
                "çeviri için metniniz yaklaşık kaç kelime "
                "veya kaç sayfa?"
            )

        # ---------------------------------------------
        # 2. AŞAMA
        # Kelime sayısı var
        # Teslim tarihi yok
        # ---------------------------------------------

        if (
            has_quantity
            and not has_delivery_date
        ):
            return (
                "Anladım. Çeviri metninizin yaklaşık "
                "kelime/sayfa sayısını not aldım. "
                "Çevirinin teslim edilmesini istediğiniz "
                "bir tarih var mı?"
            )

        # ---------------------------------------------
        # 3. AŞAMA
        # Kelime sayısı + teslim tarihi var
        # ---------------------------------------------

        if (
            has_quantity
            and has_delivery_date
        ):
            return (
                "Harika! Çeviri yönü, metin türü, "
                "metin uzunluğu ve teslim süresini "
                "aldım. Size özel teklif almak için "
                "\"Teklif Al\" bölümünden iletişim "
                "bilgilerinizi bırakabilirsiniz."
            )

        # ---------------------------------------------
        # GEMINI YOKSA
        # ---------------------------------------------

        if not self.client:
            return self.fallback_response(user_message)

        # ---------------------------------------------
        # GEMINI PROMPT
        # ---------------------------------------------

        prompt = Config.BUSINESS_CONTEXT + """

SEN TRANSILATION'IN AKILLI SATIŞ ASİSTANISIN.

Kullanıcının çeviri ihtiyacını anlamasına ve teklif
sürecine yönlendirilmesine yardımcı ol.

KURALLAR:

1. Türkçe, doğal, kısa ve profesyonel konuş.

2. Önceki mesajlarda verilen bilgileri hatırla.

3. Daha önce verilen bilgileri tekrar sorma.

4. Şu bilgileri takip et:
- Kaynak dil
- Hedef dil
- Metin türü
- Kelime veya sayfa sayısı
- Teslim tarihi

5. Kullanıcı aynı mesajda birden fazla bilgi verdiyse
hepsini dikkate al.

6. Gereksiz soru sorma.

7. Mümkünse yalnızca BİR soru sor.

8. Fiyat sorulursa kesin veya uydurma fiyat verme.

9. Gerekli bilgiler tamamlandığında kullanıcıyı
"Teklif Al" bölümüne yönlendir.

10. Kullanıcı adını veya telefonunu kendisi verdiyse
tekrar isteme.

11. Kısa cevaplar ver.

"""

        # ---------------------------------------------
        # KONUŞMA GEÇMİŞİ
        # ---------------------------------------------

        if conversation_history:

            prompt += "\n--- KONUŞMA GEÇMİŞİ ---\n"

            for item in conversation_history:

                role = item.get("role", "")
                content = item.get("content", "").strip()

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

ÖNEMLİ:

Önceki konuşmada verilmiş bilgileri tekrar sorma.

Eksik olan en önemli bilgiyi belirle.

Mümkünse yalnızca bir soru sor.

Kısa ve doğal Türkçe cevap ver.
"""

        # ---------------------------------------------
        # GEMINI
        # ---------------------------------------------

        try:

            response = self.client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt
            )

            if response and response.text:
                return response.text.strip()

            return self.fallback_response(user_message)

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

    # ---------------------------------------------
    # LEAD KAYDET
    # ---------------------------------------------

    def save_lead(self, name, phone, message):

        if not name or not phone:
            return None

        return create_lead(
            name=name,
            phone=phone,
            message=message
        )

    # ---------------------------------------------
    # FALLBACK
    # ---------------------------------------------

    def context_fallback(
        self,
        user_message,
        conversation_history=None
    ):

        history = conversation_history or []

        combined = " ".join(
            item.get("content", "")
            for item in history
            if item.get("content")
        )

        combined += " " + user_message

        text = combined.lower()

        has_quantity = bool(
            re.search(
                r"\b\d+\s*(kelime|word|sayfa)\b",
                text
            )
        )

        if has_quantity:
            return (
                "Anladım. Çeviri metninizin yaklaşık "
                "kelime/sayfa sayısını not aldım. "
                "Çevirinin teslim edilmesini istediğiniz "
                "bir tarih var mı?"
            )

        if (
            "ingilizce" in text
            and "türkçe" in text
            and (
                "akademik" in text
                or "çeviri" in text
            )
        ):
            return (
                "Harika! İngilizce → Türkçe akademik "
                "çeviri için metniniz yaklaşık kaç kelime "
                "veya kaç sayfa?"
            )

        return (
            "Merhaba! 👋 Ben Transilation'ın Akıllı Satış "
            "Asistanıyım. Çeviri ihtiyacınızı belirlemenize "
            "ve teklif sürecine yardımcı olabilirim. "
            "Nasıl bir çeviriye ihtiyacınız var?"
        )

    # ---------------------------------------------
    # BASİT FALLBACK
    # ---------------------------------------------

    def fallback_response(self, user_message):

        return self.context_fallback(
            user_message,
            []
        )


    def yanit_uret(self, user_message, conversation_history=None):
        return self.get_response(user_message, conversation_history)


ai_service = AIService()