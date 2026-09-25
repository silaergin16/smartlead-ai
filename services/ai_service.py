import os

import google.generativeai as genai


class AIServiceError(Exception):
    """Raised when the AI service cannot produce a response."""


class AIService:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.model = self._get_active_model()
        else:
            self.model = None

        self.system_prompt = os.getenv(
            "BUSINESS_CONTEXT",
            "Sen Transilation şirketinin akıllı satış asistanısın. Çeviri hizmetleri hakkında kibar, profesyonel ve yönlendirici Türkçe bilgiler ver, kullanıcıyı teklif almaya yönlendir."
        )

    def _get_active_model(self):
        try:
            available_models = [
                model.name
                for model in genai.list_models()
                if "generateContent" in model.supported_generation_methods
            ]

            preferred_models = [
                "models/gemini-1.5-flash",
                "models/gemini-1.5-pro",
                "models/gemini-pro",
            ]
            for preferred_model in preferred_models:
                if preferred_model in available_models:
                    return genai.GenerativeModel(preferred_model)

            if available_models:
                return genai.GenerativeModel(available_models[0])
        except Exception:
            pass

        return genai.GenerativeModel("gemini-1.5-flash")

    def generate_response(self, mesaj, gecmis=None):
        if not self.model:
            return "Gemini API anahtarı ayarlanmamış. Lütfen GEMINI_API_KEY ortam değişkenini kontrol edin."

        try:
            prompt_content = f"{self.system_prompt}\n\nKullanıcı Mesajı: {mesaj}"
            response = self.model.generate_content(prompt_content)
            return response.text
        except Exception as error:
            return f"Gemini yanıt üretirken hata oluştu: {error}"

    def yanit_uret(self, mesaj, gecmis=None):
        return self.generate_response(mesaj, gecmis)


ai_service = AIService()