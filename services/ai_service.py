import os
import requests
from flask import current_app


class AIServiceError(Exception):
    """Yapay zeka servis çağrılarında fırlatılan özel hata sınıfı."""
    pass


class AIService:
    """Yapay Zeka API entegrasyonunu yöneten izole servis katmanı."""

    GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
    DEFAULT_MODEL = "llama-3.1-8b-instant"

    def yanit_uret(self, mesaj: str, gecmis: list = None) -> str:
        """Kullanıcı mesajını alır, sistem talimatı ile birleştirip yanıt üretir."""
        api_key = current_app.config.get('GROQ_API_KEY') or os.environ.get('GROQ_API_KEY')

        # 1. API Anahtarı Yoksa Güvenli Fallback
        if not api_key or api_key.strip() == "":
            return "[Demo Modu] GROQ_API_KEY bulunamadı. Lütfen .env dosyanıza geçerli bir API anahtarı ekleyin."

        business_context = current_app.config.get('BUSINESS_CONTEXT', 'Sen kibar ve yardımsever bir asistansın.')

        # 2. Mesaj Yapısını Oluşturma
        messages = [{"role": "system", "content": business_context}]

        if gecmis and isinstance(gecmis, list):
            for item in gecmis:
                if isinstance(item, dict) and "role" in item and "content" in item:
                    messages.append({"role": item["role"], "content": item["content"]})

        messages.append({"role": "user", "content": mesaj})

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.DEFAULT_MODEL,
            "messages": messages,
            "temperature": 0.7
        }

        # 3. Güvenli API Çağrısı ve Hata Yönetimi
        try:
            response = requests.post(
                self.GROQ_ENDPOINT,
                headers=headers,
                json=payload,
                timeout=12
            )

            if response.status_code != 200:
                raise AIServiceError(f"AI Servisi geçici olarak kullanılamıyor (Kod: {response.status_code}).")

            data = response.json()

            if "choices" in data and len(data["choices"]) > 0:
                cevap = data["choices"][0]["message"]["content"]
                if cevap:
                    return cevap

            raise AIServiceError("AI servisinden geçersiz/boş yanıt döndü.")

        except requests.Timeout:
            raise AIServiceError("AI servisine yapılan istek zaman aşımına uğradı (Timeout).")
        except requests.RequestException as e:
            raise AIServiceError(f"Bağlantı hatası oluştu: {str(e)}")


# Tekil nesne
ai_service = AIService()