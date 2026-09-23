import os

from flask import Flask, render_template, jsonify, request, session

app = Flask(__name__)
app.secret_key = "transilation-smart-assistant"


# ==================================================
# SAYFALAR
# ==================================================

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/discover")
def discover():
    return render_template("discover.html")


@app.route("/translate")
def translate():
    return render_template("translate.html")


@app.route("/book/jane-eyre")
def jane_eyre():
    return render_template("jane_eyre.html")


@app.route("/book/great-gatsby")
def great_gatsby():
    return render_template("great_gatsby.html")


@app.route("/book/room-of-ones-own")
def room_of_ones_own():
    return render_template("room_of_ones_own.html")


@app.route("/assistant")
def assistant():
    return render_template("assistant.html")


# ==================================================
# AKILLI SATIŞ ASİSTANI
# ==================================================

@app.route("/assistant/message", methods=["POST"])
def assistant_message():

    data = request.get_json() or {}

    message = data.get("message", "").strip().lower()

    # Türkçe karakterleri daha güvenli kontrol etmek için
    normalized = message.replace("i̇", "i")


    # ==================================================
    # ÇEVİRİ BAŞLANGICI
    # ==================================================

    if (
        "çeviri hizmeti" in normalized
        or "çeviri almak" in normalized
        or normalized == "çeviri"
    ):

        session["step"] = "translation_type"
        session["translation"] = {}

        return jsonify({
            "message":
            "Elbette. Size en uygun çeviri hizmetini belirleyelim. Öncelikle metninizin türünü seçin.",

            "options": [
                "Akademik çeviri",
                "Edebi çeviri",
                "Web sitesi çevirisi",
                "Genel çeviri"
            ]
        })


    # ==================================================
    # METİN TÜRÜ
    # ==================================================

    if session.get("step") == "translation_type":

        if "akademik" in normalized:
            text_type = "Akademik"

        elif "edebi" in normalized:
            text_type = "Edebi"

        elif "web" in normalized:
            text_type = "Web sitesi"

        else:
            text_type = "Genel"

        session["translation"]["text_type"] = text_type
        session["step"] = "source_language"

        return jsonify({
            "message":
            f"{text_type} çeviri seçildi. Şimdi kaynak dili seçelim. Metniniz hangi dilde?",

            "options": [
                "İngilizce",
                "Türkçe",
                "Fransızca",
                "Almanca",
                "İspanyolca"
            ]
        })


    # ==================================================
    # KAYNAK DİL
    # ==================================================

    if session.get("step") == "source_language":

        if "ingilizce" in normalized:
            source_language = "İngilizce"

        elif "türkçe" in normalized or "turkce" in normalized:
            source_language = "Türkçe"

        elif "fransızca" in normalized or "fransizca" in normalized:
            source_language = "Fransızca"

        elif "almanca" in normalized:
            source_language = "Almanca"

        elif "ispanyolca" in normalized or "ispanyolca" in normalized:
            source_language = "İspanyolca"

        else:
            return jsonify({
                "message":
                "Kaynak dili anlayamadım. Lütfen aşağıdaki seçeneklerden birini seçin.",

                "options": [
                    "İngilizce",
                    "Türkçe",
                    "Fransızca",
                    "Almanca",
                    "İspanyolca"
                ]
            })

        session["translation"]["source_language"] = source_language
        session["step"] = "target_language"

        return jsonify({
            "message":
            f"Kaynak diliniz {source_language}. Şimdi hedef dili seçelim. Metniniz hangi dile çevrilsin?",

            "options": [
                "Türkçe",
                "İngilizce",
                "Fransızca",
                "Almanca",
                "İspanyolca"
            ]
        })


    # ==================================================
    # HEDEF DİL
    # ==================================================

    if session.get("step") == "target_language":

        if "ingilizce" in normalized:
            target_language = "İngilizce"

        elif "türkçe" in normalized or "turkce" in normalized:
            target_language = "Türkçe"

        elif "fransızca" in normalized or "fransizca" in normalized:
            target_language = "Fransızca"

        elif "almanca" in normalized:
            target_language = "Almanca"

        elif "ispanyolca" in normalized or "ispanyolca" in normalized:
            target_language = "İspanyolca"

        else:
            return jsonify({
                "message":
                "Hedef dili anlayamadım. Lütfen aşağıdaki seçeneklerden birini seçin.",

                "options": [
                    "Türkçe",
                    "İngilizce",
                    "Fransızca",
                    "Almanca",
                    "İspanyolca"
                ]
            })

        session["translation"]["target_language"] = target_language
        session["step"] = "word_count"

        return jsonify({
            "message":
            "Harika. Şimdi metninizin yaklaşık uzunluğunu öğrenelim.",

            "options": [
                "1.000 kelimeden az",
                "1.000 - 5.000 kelime",
                "5.000 - 10.000 kelime",
                "10.000+ kelime"
            ]
        })


    # ==================================================
    # KELİME SAYISI
    # ==================================================

    if session.get("step") == "word_count":

        if "1.000 kelimeden az" in normalized:
            word_count = "1.000 kelimeden az"

        elif "1.000 - 5.000" in normalized:
            word_count = "1.000 - 5.000 kelime"

        elif "5.000 - 10.000" in normalized:
            word_count = "5.000 - 10.000 kelime"

        elif "10.000" in normalized:
            word_count = "10.000+ kelime"

        else:
            return jsonify({
                "message":
                "Lütfen metniniz için uygun kelime aralığını seçin.",

                "options": [
                    "1.000 kelimeden az",
                    "1.000 - 5.000 kelime",
                    "5.000 - 10.000 kelime",
                    "10.000+ kelime"
                ]
            })

        session["translation"]["word_count"] = word_count
        session["step"] = "delivery"

        return jsonify({
            "message":
            "Son olarak teslim süresini belirleyelim. Hangi seçeneği tercih edersiniz?",

            "options": [
                "Standart teslim",
                "Hızlı teslim",
                "Acil teslim"
            ]
        })


    # ==================================================
    # TESLİM SÜRESİ
    # ==================================================

    if session.get("step") == "delivery":

        if "standart" in normalized:
            delivery = "Standart teslim"

        elif "hızlı" in normalized or "hizli" in normalized:
            delivery = "Hızlı teslim"

        elif "acil" in normalized:
            delivery = "Acil teslim"

        else:
            return jsonify({
                "message":
                "Lütfen teslim süresi için seçeneklerden birini seçin.",

                "options": [
                    "Standart teslim",
                    "Hızlı teslim",
                    "Acil teslim"
                ]
            })

        session["translation"]["delivery"] = delivery

        info = session["translation"]

        # Hizmet önerisi
        if info["text_type"] == "Akademik":
            recommended_service = "Profesyonel Akademik Çeviri"

        elif info["text_type"] == "Edebi":
            recommended_service = "Profesyonel Edebi Çeviri"

        elif info["text_type"] == "Web sitesi":
            recommended_service = "Web Sitesi Çeviri Hizmeti"

        else:
            recommended_service = "Profesyonel Genel Çeviri"

        session["step"] = "completed"

        return jsonify({
            "message":
            f"""
İhtiyacınızı belirledim.

📄 Metin türü: {info["text_type"]}
🌍 Dil çifti: {info["source_language"]} → {info["target_language"]}
📝 Metin uzunluğu: {info["word_count"]}
⏱️ Teslim tercihi: {info["delivery"]}

⭐ Önerilen hizmet:
{recommended_service}

Transilation ekibi, projenizin detaylarını inceleyerek size uygun teklif ve teslim planını oluşturabilir.
""",

            "options": [
                "Teklif almak istiyorum",
                "Yeni çeviri talebi",
                "Ana sayfaya dön"
            ]
        })


    # ==================================================
    # TEKLİF
    # ==================================================

    if "teklif almak" in normalized or "teklif" in normalized:

        return jsonify({
            "message":
            """
Teklif sürecine geçebilirsiniz.

Transilation ekibine metninizi, dil çiftini, kelime sayısını ve istediğiniz teslim süresini ileterek projeniz için özel teklif talep edebilirsiniz.
""",

            "options": [
                "Yeni çeviri talebi",
                "Ana sayfaya dön"
            ]
        })


    # ==================================================
    # YENİ ÇEVİRİ
    # ==================================================

    if "yeni çeviri" in normalized:

        session.clear()

        return jsonify({
            "message":
            "Yeni bir çeviri ihtiyacı oluşturalım. Öncelikle metninizin türünü seçin.",

            "options": [
                "Akademik çeviri",
                "Edebi çeviri",
                "Web sitesi çevirisi",
                "Genel çeviri"
            ]
        })


    # ==================================================
    # EDEBİYAT
    # ==================================================

    if (
        "edebiyat keşfetmek" in normalized
        or "edebiyat keşfi" in normalized
    ):

        session["step"] = "literature_level"

        return jsonify({
            "message":
            "Harika! Size uygun edebiyat deneyimini bulalım. Öncelikle okur grubunuzu seçin.",

            "options": [
                "Yeni başlayan okur",
                "İki dilli okur",
                "Edebiyat tutkunu"
            ]
        })


    # ==================================================
    # OKUR GRUBU
    # ==================================================

    if session.get("step") == "literature_level":

        if "başlayan" in normalized:
            recommendation = (
                "Yeni başlayan okurlar için daha anlaşılır eserlerden "
                "başlayarak kişisel bir okuma rotası oluşturabilirsiniz."
            )

        elif "iki dilli" in normalized:
            recommendation = (
                "İki dilli okurlar için eserleri iki dilde "
                "karşılaştırmalı okuyabileceğiniz bir rota oluşturabilirsiniz."
            )

        elif "tutkunu" in normalized:
            recommendation = (
                "Edebiyat tutkunları için klasik ve modern eserleri "
                "bir araya getiren daha kapsamlı bir okuma rotası oluşturabilirsiniz."
            )

        else:
            return jsonify({
                "message":
                "Lütfen aşağıdaki seçeneklerden birini seçin.",

                "options": [
                    "Yeni başlayan okur",
                    "İki dilli okur",
                    "Edebiyat tutkunu"
                ]
            })

        session.clear()

        return jsonify({
            "message": recommendation,

            "options": [
                "Çeviri hizmetleri",
                "Ana sayfaya dön"
            ]
        })


    # ==================================================
    # ÇEVİRMEN BAŞVURUSU
    # ==================================================

    if "çevirmen olarak başvurmak" in normalized:

        return jsonify({
            "message":
            "Transilation çevirmen ağına katılmak için uzmanlık alanlarınızı ve çalıştığınız dil çiftlerini belirterek başvuru sürecine başlayabilirsiniz.",

            "options": [
                "Çeviri hizmetleri",
                "Ana sayfaya dön"
            ]
        })


    # ==================================================
    # PROFESYONEL ÇEVİRİ
    # ==================================================

    if "profesyonel çeviri" in normalized:

        return jsonify({
            "message":
            "Profesyonel çeviri hizmetlerimiz akademik, edebi, web sitesi ve genel metin türlerine yönelik çözümler sunabilir.",

            "options": [
                "Çeviri hizmeti almak istiyorum",
                "Teklif almak istiyorum"
            ]
        })


    # ==================================================
    # ANA SAYFA
    # ==================================================

    if "ana sayfa" in normalized:

        session.clear()

        return jsonify({
            "message":
            "Nasıl devam etmek istersiniz?",

            "options": [
                "Çeviri hizmeti almak istiyorum",
                "Edebiyat keşfetmek istiyorum",
                "Çevirmen olarak başvurmak istiyorum"
            ]
        })


    # ==================================================
    # İLK KARŞILAMA
    # ==================================================

    return jsonify({
        "message":
        "Merhaba! Ben Transilation'ın Akıllı Satış Asistanıyım. İhtiyacınıza uygun hizmeti bulmanızda yardımcı olabilirim. Nasıl ilerlemek istersiniz?",

        "options": [
            "Çeviri hizmeti almak istiyorum",
            "Edebiyat keşfetmek istiyorum",
            "Profesyonel çeviri hakkında bilgi almak istiyorum",
            "Çevirmen olarak başvurmak istiyorum"
        ]
    })


# ==================================================
# UYGULAMAYI ÇALIŞTIR
# ==================================================

if __name__ == "__main__":
    app.run(
        debug=True,
        port=5001
    )