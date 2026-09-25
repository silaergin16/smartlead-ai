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

        prompt = Config.BUSINESS_CONTEXT + "\n\n"

        prompt += """
SEN TRANSILATION'IN AKILLI SATIŞ ASİSTANISIN.

Görevin, kullanıcıların çeviri ihtiyaçlarını anlamak ve
onları teklif alma sürecine yönlendirmektir.

KURALLAR:

1. Türkçe, doğal, samimi ve profesyonel konuş.

2. Kullanıcının mesajında verdiği bilgileri dikkatlice analiz et.

3. Kullanıcı bir bilgiyi zaten söylediyse ASLA tekrar sorma.

4. Aşağıdaki bilgileri mümkün olduğunca konuşma sırasında topla:

- Kaynak dil
- Hedef dil
- Metin türü
- Yaklaşık kelime veya sayfa sayısı
- Teslim tarihi

5. Kullanıcı aynı mesajda birden fazla bilgi verirse hepsini
hatırla ve tekrar sorma.

ÖRNEK:
Kullanıcı:
"İngilizceden Türkçeye akademik çeviri istiyorum."

Burada zaten:
- Kaynak dil: İngilizce
- Hedef dil: Türkçe
- Metin türü: Akademik

bilgileri verilmiştir.

Bu nedenle tekrar "Hangi dilden hangi dile?" veya
"Metninizin türü nedir?" diye SORMA.

Bunun yerine:
"Harika! Metniniz yaklaşık kaç kelime veya kaç sayfa?"
gibi eksik olan bir sonraki bilgiyi sor.

6. Kullanıcı kelime sayısını bilmiyorsa yaklaşık sayfa sayısını sor.

7. Kullanıcı teslim tarihini söylediyse tekrar sorma.

8. Her mesajda mümkünse yalnızca BİR soru sor.

9. Kullanıcı fiyat veya teklif sorarsa kesin fiyat uydurma.
Fiyatın dil çifti, metin türü, kelime sayısı ve teslim süresine
göre belirlendiğini belirt.

10. Kullanıcı teklif almak istediğini açıkça söylerse,
Wix'teki "Teklif Al" bölümünden iletişim bilgilerini
bırakabileceğini söyle.

11. Gereksiz kişisel bilgi isteme.

12. Kullanıcı adını veya telefonunu konuşmada kendisi verirse
bunu tekrar isteme.

13. Kısa ve anlaşılır cevaplar ver.

14. Önceki konuşmadaki bilgileri kullan ve kullanıcıya
aynı soruları tekrar sorma.

KONUŞMA ÖRNEĞİ:

Kullanıcı:
"İngilizceden Türkçeye akademik çeviri istiyorum."

Asistan:
"Harika! İngilizce → Türkçe akademik çeviri için
metniniz yaklaşık kaç kelime veya kaç sayfa?"

Kullanıcı:
"3000 kelime."

Asistan:
"Anladım. Peki çevirinin teslim edilmesini istediğiniz
bir tarih var mı?"

Kullanıcı:
"3 gün içinde."

Asistan:
"Harika, ihtiyacınızı not aldım. Size uygun teklif
almak için 'Teklif Al' bölümünden iletişim bilgilerinizi
bırakabilirsiniz."

Bu örnekteki mantığı kullan fakat cevapları kullanıcının
mesajına göre doğal şekilde oluştur.
"""

        prompt += "\n\n"

        if conversation_history:

            prompt += "ÖNCEKİ KONUŞMA:\n"

            for message in conversation_history:

                role = message.get("role", "user")
                content = message.get("content", "")

                prompt += f"{role}: {content}\n"

            prompt += "\n"

        prompt += f"""
KULLANICININ YENİ MESAJI:

{user_message}

ÖNEMLİ:
Kullanıcının yeni mesajındaki bilgileri önceki konuşmayla
birlikte değerlendir.

Zaten verilmiş bilgileri tekrar sorma.

Eksik olan en önemli BİR sonraki bilgiyi sor.

Kullanıcı teklif almak istiyorsa uygun şekilde "Teklif Al"
bölümüne yönlendir.

Şimdi doğal ve kısa bir cevap ver.
"""

        try:

            response = self.client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt
            )

            return response.text

        except Exception as error:

            print(f"Gemini API Error: {error}")

            return self.fallback_response(user_message)


    def save_lead(self, name, phone, message):

        if not name or not phone:
            return None

        return create_lead(
            name=name,
            phone=phone,
            message=message
        )


    def fallback_response(self, user_message):

        message = user_message.lower()

        if any(word in message for word in [
            "çeviri",
            "çevir",
            "translate"
        ]):

            return (
                "Harika! Çeviri hizmetiniz için size yardımcı "
                "olabilirim. Metniniz yaklaşık kaç kelime veya "
                "kaç sayfa?"
            )

        if any(word in message for word in [
            "teklif",
            "fiyat",
            "ücret"
        ]):

            return (
                "Size uygun bir teklif hazırlayabilmemiz için "
                "çeviri yönünü, metin türünü ve yaklaşık "
                "kelime sayısını öğrenmemiz gerekiyor."
            )

        return (
            "Merhaba! 👋 Ben Transilation'ın Akıllı Satış "
            "Asistanıyım. Çeviri ihtiyacınızı belirlemenize "
            "ve teklif sürecine yardımcı olabilirim. "
            "Nasıl bir çeviriye ihtiyacınız var?"
        )


ai_service = AIService()