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
def read_text_file(file_path):
    # Open and read the text file
    try:
        with open(file_path, 'r') as file:
            content = file.read()
            print(f"Content of the file:\n{content}")
            return content
    except FileNotFoundError:
        print(f"The file '{file_path}' was not found.")
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")


def generate_response(filename):
    promp=read_text_file(filename+".wav.txt")

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
