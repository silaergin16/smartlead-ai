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

        """
        Gemini AI ile kullanıcı mesajına cevap üretir.
        """

        if not self.client:
            return self.fallback_response(user_message)

        prompt = Config.BUSINESS_CONTEXT + "\n\n"

        prompt += """
ÖNEMLİ: SEN TRANSILATION'IN AKILLI SATIŞ ASİSTANISIN.

Amacın kullanıcıya çeviri hizmetleri hakkında yardımcı olmak
ve uygun bir teklif oluşturmak için gerekli bilgileri doğal
bir sohbet içerisinde toplamaktır.

KONUŞMA KURALLARI:

1. Kullanıcıyla Türkçe, doğal, samimi ve profesyonel konuş.

2. Kullanıcı bir çeviri talebinden bahsettiğinde öncelikle
   ihtiyacını anlamaya çalış.

3. Gerekli bilgileri şu sırayla mümkün olduğunca doğal şekilde
   toplamaya çalış:

   - Kaynak dil
   - Hedef dil
   - Metin türü
   - Yaklaşık kelime sayısı veya sayfa sayısı
   - İstenen teslim tarihi

4. Kullanıcı zaten verdiği bir bilgiyi tekrar sorma.

5. Kullanıcıdan aynı anda çok fazla soru isteme.
   Genellikle tek seferde bir soru sor.

6. Kullanıcı örneğin:
   "İngilizceden Türkçeye akademik çeviri"
   derse, bu bilgileri tekrar sormak yerine eksik olan
   bilgiyi sor.

   Örneğin:
   "Harika! Akademik İngilizce → Türkçe çeviri için
   yaklaşık kaç kelimelik bir metniniz var?"

7. Kullanıcı kelime sayısını bilmiyorsa yaklaşık sayfa
   sayısını sorabilirsin.

8. Kullanıcı fiyat veya teklif sorarsa gerekli bilgileri
   mümkün olduğunca tamamla ve ardından teklif almak için
   iletişim formunu kullanabileceğini belirt.

9. Kullanıcı telefon numarası veya adını kendisi verirse
   bunu konuşma bağlamında dikkate al.

10. Gereksiz kişisel bilgi isteme.

11. Kullanıcı henüz teklif istemediyse konuşmayı zorla
    iletişim bilgilerine yönlendirme.

12. Kullanıcı teklif almak istediğini açıkça söylerse:
    "Teklif Al" bölümünden iletişim bilgilerini bırakabileceğini
    kısa ve net şekilde belirt.

13. Kesin fiyat verme. Fiyatın metin türü, kelime sayısı,
    dil çifti ve teslim süresi gibi faktörlere göre
    belirlendiğini söyle.

14. Cevapların kısa ve anlaşılır olsun.

15. Kullanıcı aynı konu hakkında devam ediyorsa önceki
    konuşmadaki bilgileri kullan.

ÖRNEK KONUŞMA:

Kullanıcı:
"İngilizceden Türkçeye akademik çeviri yaptırmak istiyorum."

Asistan:
"Tabii! İngilizce → Türkçe akademik çeviri konusunda
yardımcı olabilirim. Metniniz yaklaşık kaç kelime veya
kaç sayfa?"

Kullanıcı:
"Yaklaşık 3000 kelime."

Asistan:
"Anladım. Peki çevirinin teslim edilmesini istediğiniz
bir tarih var mı?"

Kullanıcı:
"3 gün içinde."

Asistan:
"Harika. İhtiyacınızı not aldım: İngilizce → Türkçe,
akademik çeviri, yaklaşık 3000 kelime ve 3 günlük teslim
süresi. Size özel teklif almak için aşağıdaki
'Teklif Al' bölümünden iletişim bilgilerinizi
bırakabilirsiniz."

Bu örnekleri birebir tekrarlamak zorunda değilsin.
Kullanıcının mesajına göre doğal bir konuşma oluştur.

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

Şimdi kullanıcıya doğal, kısa ve profesyonel bir cevap ver.
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

        """
        Kullanıcı bilgilerini veritabanına kaydeder.
        """

        if not name or not phone:

            return None

        return create_lead(

            name=name,

            phone=phone,

            message=message

        )


    def fallback_response(self, user_message):

        """
        Gemini bağlantısı olmadığında kullanılacak
        temel cevap sistemi.
        """

        message = user_message.lower()


        if any(word in message for word in [

            "çeviri",
            "çevir",
            "translate"

        ]):

            return (

                "Tabii! Size yardımcı olabilirim. "

                "Öncelikle çevirinin hangi dilden hangi dile "

                "yapılacağını ve metninizin türünü öğrenebilir miyim?"

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