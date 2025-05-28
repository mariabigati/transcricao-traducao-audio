import streamlit as st
import speech_recognition as sr
from pydub import AudioSegment
from pydub.utils import which  
import google.generativeai as genai
import os
from dotenv import load_dotenv, find_dotenv
import time

# Estilo mágico e natureza
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Caveat:wght@500&display=swap');

    html, body, [class*="css"]  {
        font-family: 'Caveat', cursive;
        background-color: #F8F1E5;
    }
    header {
        background-color: rgba(0, 0, 0, 0.1) !important;
        backdrop-filter: blur(10px) !important;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3) !important;
        }

    .stApp {
        background-image: url('https://images3.alphacoders.com/558/thumb-1920-558308.gif');
        background-size: cover;
        background-repeat: no-repeat;
    }
            
    .stApp::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0,0,0,0.1);
        z-index: 0;
    }

    h1, h2, h3 {
        color: #C44F4F;
    }

    .stButton > button {
        background-color: #A8BCA1;
        border: none;
        color: white;
        padding: 10px 20px;
        border-radius: 10px;
        font-weight: bold;
        transition: all 0.3s ease-in-out;
    }

    .stButton > button:hover {
        background-color: #8AAE8D;
        transform: scale(1.05);
    }
    </style>
""", unsafe_allow_html=True)

# FFmpeg fix
AudioSegment.converter = which("ffmpeg")

# Variáveis .env
_ = load_dotenv(find_dotenv())
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    st.error("Configure GOOGLE_API_KEY no .env.")
    st.stop()

genai.configure(api_key=GOOGLE_API_KEY)


progress_placeholder = st.empty()

# Transcrição em blocos
def transcribe_audio_offline(audio_file):
    try:
        with open("temp_audio.mp3", "wb") as f:
            f.write(audio_file.read())
        sound = AudioSegment.from_mp3("temp_audio.mp3")
        sound.export("temp_audio.wav", format="wav", parameters=["-ar", "16000", "-ac", "1"])

        r = sr.Recognizer()
        with sr.AudioFile("temp_audio.wav") as source:
            full_audio = r.record(source)

        chunk_size = 30 * 16000
        chunks = [full_audio.frame_data[i:i+chunk_size*2] for i in range(0, len(full_audio.frame_data), chunk_size*2)]

        transcribed_text = ""
        status_placeholder = st.empty()
        status_placeholder.subheader("Transcrevendo com magia...")

        for i, chunk_data in enumerate(chunks):
            audio_chunk = sr.AudioData(chunk_data, sample_rate=16000, sample_width=2)
            try:
                part = r.recognize_google(audio_chunk, language="en-US")
                transcribed_text += f"{part} "
            except sr.UnknownValueError:
                transcribed_text += "[inaudível] "
            except sr.RequestError as e:
                st.error(f"Erro de serviço: {e}")
                return None

            update_progress_bar(int((i + 1) / len(chunks) * 100))
            time.sleep(0.1)

        os.remove("temp_audio.mp3")
        os.remove("temp_audio.wav")

        # Limpa placeholders após a transcrição
        status_placeholder.empty()
        progress_placeholder.empty()

        return transcribed_text.strip()

    except Exception as e:
        st.error(f"Erro na transcrição: {e}")
        return None
    
def update_progress_bar(percent):
    progress_bar_html = f"""
    <div style="
        position: fixed;
        bottom: 20px;
        left: 50%;
        transform: translateX(-50%);
        width: 80%;
        z-index: 9999;
        background: linear-gradient(135deg, #ffd6f3, #ffe6f9);
        border-radius: 12px;
        padding: 6px;
        box-shadow: 0 0 15px rgba(255, 105, 180, 0.7), 0 0 25px rgba(255, 182, 193, 0.5);
        border: 1px solid #ffa6d6;
        backdrop-filter: blur(6px);
    ">
        <div style="
            width: {percent}%;
            background: linear-gradient(90deg, #ff4f9f, #ff8fd8);
            height: 22px;
            border-radius: 10px;
            box-shadow: 0 0 10px #ff69b4, 0 0 20px #ffb6c1;
            animation: glow 1.5s infinite alternate;
            transition: width 0.4s ease-in-out;
        "></div>
        <p style="text-align: center; margin: 6px 0 0 0; font-size: 15px; color: #850f48; font-weight: bold;">
            ✨ {percent}% completo ✨
        </p>
    </div>
"""
    progress_placeholder.markdown(progress_bar_html, unsafe_allow_html=True)

# Tradução com Gemini
def translate_text_gemini(text, target_language="pt-BR"):
    try:
        model = genai.GenerativeModel("models/gemini-1.5-flash")
        prompt = f"Translate the following text to {target_language}:\n{text}"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"Erro na tradução com Gemini: {e}")
        return None

# Aplicação principal
def main():
    st.header("Transcrição & Tradução com Gemini")

    uploaded_file = st.file_uploader("🎧 Envie um áudio (MP3)", type=["mp3"])

    if uploaded_file:
        st.audio(uploaded_file, format="audio/mp3")
        transcription = transcribe_audio_offline(uploaded_file)

        if transcription:
            st.subheader("Transcrição:")
            st.write(transcription)

            target_language = st.selectbox("Traduzir para:", ["pt-BR", "es", "fr", "de", "it"])
            with st.spinner("🔮 Traduzindo com magia..."):
                translation = translate_text_gemini(transcription, target_language)

            if translation:
                st.subheader(f"Tradução ({target_language}):")
                st.write(translation)
            else:
                st.error("❌ Tradução falhou.")
        else:
            st.error("❌ Transcrição falhou.")

if __name__ == "__main__":
    main()
