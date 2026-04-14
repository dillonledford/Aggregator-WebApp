from flask import Flask, render_template, request
from google import genai
from system_prompts import PROMPTS

app = Flask(__name__)
client = genai.Client(api_key="AIzaSyC2B05H6MMB9Q9mdhZbiChCHubt6HfVQCM")

@app.route("/", methods=["GET", "POST"])
def index():
    output = None
    if request.method == "POST":
        prompt = request.form.get("prompt")
        mode = request.form.get("mode", "synthesize")
        system_instruction = PROMPTS[mode]
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt,
            config={"system_instruction": system_instruction}
        )
        output = response.text
    return render_template("index.html", output=output)

if __name__ == "__main__":
    app.run(debug=True)
