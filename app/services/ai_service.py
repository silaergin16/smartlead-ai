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

        if not self.client:
            return self.fallback_response(user_message)


        conversation_history = conversation_history or []


        prompt = Config.BUSINESS_CONTEXT + """

SEN TRANSILATION'IN AKILLI SATIŞ ASİSTANISIN.

Kullanıcının çeviri ihtiyacını anlamak ve teklif sürecine
yönlendirmek için yardımcı oluyorsun.

KONUŞMA KURALLARI:

1. Türkçe, doğal, kısa ve profesyonel konuş.

2. Kullanıcının daha önce verdiği bilgileri HATIRLA.

3. Kullanıcı bir bilgiyi zaten verdiyse ASLA tekrar sorma.

4. Özellikle şu bilgileri takip et:

- Kaynak dil
- Hedef dil
- Metin türü
- Kelime veya sayfa sayısı
- Teslim tarihi

5. Kullanıcı aynı mesajda birden fazla bilgi verdiyse
hepsini aynı anda hatırla.

6. Örneğin kullanıcı:

"İngilizceden Türkçeye akademik çeviri istiyorum."

derse şu bilgiler zaten bellidir:

Kaynak dil = İngilizce
Hedef dil = Türkçe
Metin türü = Akademik

Bu bilgileri tekrar sorma.

Bunun yerine yalnızca eksik olan bir sonraki önemli bilgiyi sor.

Örneğin:

"Harika! Metniniz yaklaşık kaç kelime veya kaç sayfa?"

7. Kullanıcı:

"3000 kelime"

derse kelime sayısının 3000 olduğunu hatırla.

Önceki bilgilerle birlikte düşün:

Kaynak = İngilizce
Hedef = Türkçe
Tür = Akademik
Kelime = 3000

Bu durumda kaynak dili, hedef dili veya metin türünü
TEKRAR SORMA.

Bunun yerine teslim tarihini sor:

"Anladım. Çevirinin teslim edilmesini istediğiniz bir tarih var mı?"

8. Kullanıcı teslim tarihini de verdiyse artık gerekli bilgilerin
tamamlandığını belirt ve "Teklif Al" bölümüne yönlendir.

9. Her mesajda mümkünse yalnızca BİR soru sor.

10. Kullanıcı fiyat sorarsa kesin veya uydurma bir fiyat verme.

11. Kullanıcı teklif almak istediğini söylerse
"Teklif Al" bölümünden iletişim bilgilerini bırakabileceğini söyle.

12. Kullanıcı adını veya telefonunu konuşma içinde kendisi verirse
tekrar isteme.

13. Gereksiz kişisel bilgi isteme.

14. Kullanıcıyla konuşurken önceki mesajları dikkate al.

15. Kısa cevaplar ver.

ŞİMDİ AŞAĞIDAKİ KONUŞMA GEÇMİŞİNİ DİKKATLİCE İNCELE.
"""

        # Konuşma geçmişini açık ve düzenli şekilde ekle
        if conversation_history:

            prompt += "\n\n--- KONUŞMA GEÇMİŞİ ---\n"

            for item in conversation_history:

                role = item.get("role", "")
                content = item.get("content", "")

                if not content:
                    continue

                if role == "user":
                    prompt += f"KULLANICI: {content}\n"

                elif role == "assistant":
                    prompt += f"ASİSTAN: {content}\n"

            prompt += "\n--- KONUŞMA GEÇMİŞİ SONU ---\n"


        prompt += f"""

KULLANICININ ŞU ANKİ MESAJI:

{user_message}

ÖNEMLİ:

Önce konuşma geçmişini incele.

Kullanıcının daha önce verdiği bilgileri çıkar.

Bu bilgilerden hiçbirini tekrar sorma.

Eksik olan en önemli bilgiyi belirle.

Mümkünse yalnızca BİR soru sor.

Eğer gerekli bilgiler tamamlandıysa kullanıcıyı
"Teklif Al" bölümüne yönlendir.

Şimdi kullanıcıya doğal ve kısa bir Türkçe cevap ver.
"""


        try:

            response = self.client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt
            )

            if response and response.text:

                return response.text.strip()

            return (
                "Anladım. Çeviri talebinizle ilgili "
                "bir sonraki bilgiyi paylaşabilir misiniz?"
            )


        except Exception as error:

            print(
                f"Gemini API Error: {type(error).__name__}: {error}",
                flush=True
            )

            return self.context_fallback(
                user_message,
                conversation_history
            )


    def save_lead(self, name, phone, message):

        if not name or not phone:
            return None

        return create_lead(
            name=name,
            phone=phone,
            message=message
        )


    def context_fallback(
        self,
        user_message,
        conversation_history=None
    ):

        """
        Gemini geçici olarak hata verirse bile
        konuşmanın mantığını koruyan basit fallback.
        """

        history = conversation_history or []

        combined = " ".join(
            item.get("content", "")
            for item in history
            if item.get("content")
        )

        combined += " " + user_message

        text = combined.lower()


        # Kelime sayısı verildiyse teslim tarihini sor
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


        # Çeviri bilgileri varsa kelime sayısını sor
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


    def fallback_response(self, user_message):

        return self.context_fallback(
            user_message,
            []
        )


ai_service = AIService()