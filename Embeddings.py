from flask import Flask, request, jsonify
from sentence_transformers import SentenceTransformer

app = Flask(__name__)
model = SentenceTransformer('all-MiniLM-L6-v2')

@app.route('/generate-embeddings', methods=['POST'])
def generate_embeddings():
    data = request.json

    if not data or not all(k in data for k in ["definition", "causes", "effects"]):
        return jsonify({"error": "Missing required keys: 'definition', 'causes', 'effects'"}), 400

    # Flatten all text
    all_texts = [data["definition"]] + data["causes"] + data["effects"]
    embeddings = model.encode(all_texts)

    # Reconstruct with embeddings
    context_with_embeddings = {
        "definition": {
            "text": data["definition"],
            "embedding": embeddings[0].tolist()
        },
        "causes": [
            {
                "text": data["causes"][i],
                "embedding": embeddings[i+1].tolist()
            } for i in range(len(data["causes"]))
        ],
        "effects": [
            {
                "text": data["effects"][j],
                "embedding": embeddings[j+1+len(data["causes"])].tolist()
            } for j in range(len(data["effects"]))
        ]
    }

    return jsonify(context_with_embeddings)

if __name__ == '__main__':
    app.run(debug=False)
