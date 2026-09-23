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
        ÖNEMLİ SATIŞ ASİSTANI KURALLARI:

        Kullanıcı çeviri hizmetiyle ilgileniyorsa konuşmayı
        doğal şekilde ilerlet.

        Öncelikle kullanıcının:
        - metin türünü,
        - kaynak dilini,
        - hedef dilini,
        - yaklaşık kelime sayısını,
        - teslim süresini

        anlamaya çalış.

        Kullanıcı teklif almak istediğini belirtirse,
        iletişim bilgilerini bırakabileceğini söyle.

        Kullanıcıdan aynı anda çok fazla soru isteme.
        Konuşmayı doğal ve kısa tut.

        Kullanıcı adını verirse bunu hatırla.
        Kullanıcı telefon numarasını verirse bunu da konuşma
        bağlamında dikkate al.

        Kullanıcı telefon numarasını paylaşmadan önce
        telefon numarası istemen gerekiyorsa açıkça neden
        istediğini belirt.

        Kullanıcıdan gereksiz kişisel bilgi isteme.
        """

        prompt += "\n\n"

        if conversation_history:
            prompt += "Önceki konuşma:\n"

            for message in conversation_history:
                role = message.get("role", "user")
                content = message.get("content", "")

                prompt += f"{role}: {content}\n"

            prompt += "\n"

        prompt += f"Kullanıcının yeni mesajı:\n{user_message}"

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
                "Tabii! Size uygun çeviri hizmetini "
                "belirleyebilmem için birkaç bilgiye "
                "ihtiyacım var. Metninizin türü nedir?"
            )

        if any(word in message for word in [
            "teklif",
            "fiyat",
            "ücret"
        ]):
            return (
                "Size uygun bir teklif hazırlayabilmemiz "
                "için adınızı ve telefon numaranızı "
                "paylaşabilirsiniz."
            )

        return (
            "Merhaba! Ben Transilation Akıllı Satış "
            "Asistanıyım. Çeviri hizmetiniz konusunda "
            "size yardımcı olabilirim. Ne tür bir "
            "çeviri ihtiyacınız var?"
        )


ai_service = AIService()