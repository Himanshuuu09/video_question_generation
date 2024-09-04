import os
from moviepy.editor import VideoFileClip
import speech_recognition as sr
from flask import Flask, request, jsonify
import google.generativeai as genai
from dotenv import load_dotenv
from flask_cors import CORS
import asyncio
import re

load_dotenv()

app = Flask(__name__)
CORS(app)

mcq_pattern = re.compile(
    r'\{\s*"question":\s*"([^"]*)",\s*'
    r'"option1":\s*"([^"]*)",\s*'
    r'"option2":\s*"([^"]*)",\s*'
    r'"option3":\s*"([^"]*)",\s*'
    r'"option4":\s*"([^"]*)",\s*'
    r'"answer":\s*"([^"]*)"\s*\}',
    re.DOTALL,
)
# Set your Google AI API key
genai.configure(api_key=os.environ.get("GOOGLE_AI_API_KEY"))

def convert_video_to_audio(video_path):
    # Extract file name without extension
    base_name = os.path.splitext(os.path.basename(video_path))[0]

    # Define the output audio path with the same name and .wav extension
    output_audio_path = f"{base_name}.wav"
    
    # Check if the audio file already exists
    if os.path.exists(output_audio_path):
        print(f"Audio file '{output_audio_path}' already exists. Skipping conversion.")
        return output_audio_path

    # Load the video clip
    video = VideoFileClip(video_path)

    # Extract the audio and save it
    video.audio.write_audiofile(output_audio_path)
    return output_audio_path

def convert_audio_to_text(audio_file_path):
    # Initialize recognizer class (for recognizing the speech)
    recognizer = sr.Recognizer()

    # Open the audio file
    with sr.AudioFile(audio_file_path) as source:
        # Listen to the audio file
        audio_data = recognizer.record(source)
        # Convert audio to text using Google's speech recognition
        try:
            text = recognizer.recognize_google(audio_data)
            print(f"Recognized text: {text}")
            return text
        except sr.UnknownValueError:
            print("Google Speech Recognition could not understand the audio")
        except sr.RequestError:
            print("Could not request results from Google Speech Recognition service")

def generate_response(filename):
    audio_path = convert_video_to_audio(rf"D:\video_question_generation\{filename}")
    promp = convert_audio_to_text(rf"D:\video_question_generation\{audio_path}")

    prompt = f"""Design a mcq type quiz for {promp}. Convert into json format under heading question,option1,option2,option3,option4,answer. Give answer as correct answer not as option. Give 4 questions in English language :
"""
    pattern = mcq_pattern


    model = genai.GenerativeModel(model_name="gemini-pro")
    response = model.generate_content(prompt)
    generated_text = response.text
    matches = pattern.findall(generated_text)
    mcq_data=[]
    # Print raw response to debug
    for match in matches:
                    mcq_data.append({
                        "description": match[0],
                        "options": match[1:5],
                        "answer": match[5],
                    })


    return {
        "result": mcq_data,
        "message": "all questions",
        "success": True
    },200


async def process_questions(data):
    filename = data.get("filename", "")
    if not filename:
        return {"error": "Missing data"}, 400
    else:
        mcq_data = generate_response(filename)
        return mcq_data, 200

@app.route("/video_question", methods=["POST"])
def generate_question_endpoint():
    """API endpoint to generate questions and answers."""
    data = request.json
    response, status_code = asyncio.run(process_questions(data))
    return jsonify(response), status_code

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, threaded=True)
