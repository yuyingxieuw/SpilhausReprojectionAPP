"""
Create & Manage API
"""

from flask import Flask, jsonify, request, render_template
from scripts.workflow_poly import run_program

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/process", methods=["POST"])
def process_geojson():
    data = request.get_json()
    result = run_program(data)
    return jsonify({"status": "success", "result": result})

if __name__ == "__main__":
    app.run(debug=True)
