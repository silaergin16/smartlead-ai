from google import genai

from config import Config
from app.database import create_lead


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

        # -------------------------------------------------
        # KONUŞMA GEÇMİŞİNİ ANALİZ ET
        # -------------------------------------------------

        all_messages = []

        for item in conversation_history:
            content = item.get("content", "").strip()

            if content:
                all_messages.append(content)

        # Şu anki mesajı da ekle
        all_messages.append(user_message)

        full_text = " ".join(all_messages).lower()

        # -------------------------------------------------
        # KELİME / SAYFA SAYISI VERİLDİYSE
        # -------------------------------------------------

        has_quantity = any(
            word in full_text
            for word in [
                "kelime",
                "sayfa",
                "word"
            ]
        )

        # -------------------------------------------------
        # TESLİM TARİHİ HENÜZ VERİLMEDİYSE
        # -------------------------------------------------

        delivery_words = [
            "gün",
            "hafta",
            "yarın",
            "bugün",
            "teslim",
            "cuma",
            "cumartesi",
            "pazar",
            "pazartesi",
            "salı",
            "çarşamba",
            "perşembe",
            "nisan",
            "mayıs",
            "haziran",
            "temmuz",
            "ağustos",
            "eylül",
            "ekim",
            "kasım",
            "aralık"
        ]

        has_delivery_date = any(
            word in full_text
            for word in delivery_words
        )

        # -------------------------------------------------
        # KELİME SAYISI VERİLDİYSE VE TESLİM TARİHİ YOKSA
        # GEMINI'YE BAĞLI KALMADAN DOĞRU CEVABI VER
        # -------------------------------------------------

        if has_quantity and not has_delivery_date:

            return (
                "Anladım. Çeviri metninizin yaklaşık "
                "kelime/sayfa sayısını not aldım. "
                "Çevirinin teslim edilmesini istediğiniz "
                "bir tarih var mı?"
            )

        # -------------------------------------------------
        # KAYNAK + HEDEF + METİN TÜRÜ VARSA
        # KELİME SAYISINI SOR
        # -------------------------------------------------

        has_english = "ingilizce" in full_text
        has_turkish = "türkçe" in full_text

        has_text_type = any(
            word in full_text
            for word in [
                "akademik",
                "hukuki",
                "teknik",
                "edebi",
                "ticari",
                "web sitesi",
                "makale",
                "tez",
                "belge"
            ]
        )

        if (
            has_english
            and has_turkish
            and has_text_type
            and not has_quantity
        ):

            return (
                "Harika! İngilizce → Türkçe akademik "
                "çeviri için metniniz yaklaşık kaç kelime "
                "veya kaç sayfa?"
            )

        # -------------------------------------------------
        # GEREKLİ BİLGİLER TAMAMSA
        # TEKLİF AL BÖLÜMÜNE YÖNLENDİR
        # -------------------------------------------------

        if has_quantity and has_delivery_date:

            return (
                "Harika! Çeviri yönü, metin türü, "
                "metin uzunluğu ve teslim süresini "
                "aldım. Size özel teklif almak için "
                "\"Teklif Al\" bölümünden iletişim "
                "bilgilerinizi bırakabilirsiniz."
            )

        # -------------------------------------------------
        # GEMINI YOKSA FALLBACK
        # -------------------------------------------------

        if not self.client:

            return self.fallback_response(user_message)

        # -------------------------------------------------
        # GEMINI PROMPT
        # -------------------------------------------------

        prompt = Config.BUSINESS_CONTEXT + """

SEN TRANSILATION'IN AKILLI SATIŞ ASİSTANISIN.

Kullanıcının çeviri ihtiyacını anlamasına ve teklif
sürecine yönlendirilmesine yardımcı ol.

KONUŞMA KURALLARI:

1. Türkçe, doğal, kısa ve profesyonel konuş.

2. Konuşma geçmişindeki bilgileri hatırla.

3. Kullanıcının daha önce verdiği bilgileri tekrar sorma.

4. Şu bilgileri takip et:

- Kaynak dil
- Hedef dil
- Metin türü
- Kelime veya sayfa sayısı
- Teslim tarihi

5. Kullanıcı aynı mesajda birden fazla bilgi verdiyse
hepsini dikkate al.

6. Gereksiz soru sorma.

7. Mümkünse her mesajda yalnızca BİR soru sor.

8. Fiyat sorulursa kesin veya uydurma fiyat verme.

9. Gerekli bilgiler tamamlandığında kullanıcıyı
"Teklif Al" bölümüne yönlendir.

10. Kullanıcı adını veya telefonunu kendisi verdiyse
tekrar isteme.

11. Kısa cevaplar ver.

Şimdi konuşma geçmişini ve kullanıcının son mesajını
dikkatlice değerlendir.
"""

        # -------------------------------------------------
        # GEÇMİŞİ GEMINI'YE GÖNDER
        # -------------------------------------------------

        if conversation_history:

            prompt += "\n\n--- KONUŞMA GEÇMİŞİ ---\n"

            for item in conversation_history:

                role = item.get("role", "")
                content = item.get("content", "").strip()

                if not content:
                    continue

                if role == "user":

                    prompt += (
                        f"KULLANICI: {content}\n"
                    )

                elif role == "assistant":

                    prompt += (
                        f"ASİSTAN: {content}\n"
                    )

            prompt += "\n--- KONUŞMA GEÇMİŞİ SONU ---\n"

        prompt += f"""

KULLANICININ SON MESAJI:

{user_message}

ÖNEMLİ:

Önceki konuşmada verilmiş bilgileri tekrar sorma.

Kullanıcının ihtiyacını dikkate al.

Eksik olan en önemli bilgiyi belirle.

Mümkünse yalnızca bir soru sor.

Kısa ve doğal Türkçe cevap ver.
"""

        # -------------------------------------------------
        # GEMINI
        # -------------------------------------------------

        try:

            response = self.client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt
            )

            if response and response.text:

                return response.text.strip()

            return self.fallback_response(
                user_message
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

    # -----------------------------------------------------
    # LEAD KAYDET
    # -----------------------------------------------------

    def save_lead(self, name, phone, message):

        if not name or not phone:
            return None

        return create_lead(
            name=name,
            phone=phone,
            message=message
        )

    # -----------------------------------------------------
    # FALLBACK
    # -----------------------------------------------------

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

        if any(
            word in text
            for word in [
                "kelime",
                "sayfa",
                "word"
            ]
        ):

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

        if any(
            word in text
            for word in [
                "teklif",
                "fiyat",
                "ücret"
            ]
        ):

            return (
                "Size uygun bir teklif hazırlayabilmemiz için "
                "çeviri yönü, metin türü, yaklaşık kelime sayısı "
                "ve teslim süresini öğrenmemiz gerekiyor."
            )

        return (
            "Merhaba! 👋 Ben Transilation'ın Akıllı Satış "
            "Asistanıyım. Çeviri ihtiyacınızı belirlemenize "
            "ve teklif sürecine yardımcı olabilirim. "
            "Nasıl bir çeviriye ihtiyacınız var?"
        )

    # -----------------------------------------------------
    # BASİT FALLBACK
    # -----------------------------------------------------

    def fallback_response(self, user_message):

        return self.context_fallback(
            user_message,
            []
        )


ai_service = AIService()