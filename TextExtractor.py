from flask import Flask, request, jsonify
import requests
import time
from PIL import Image
import io

app = Flask(__name__)

# Azure credentials
subscription_key = '6b2uM74mq58QMzHkU50QsZwJXDVoUuklAi6fqiob6b7XiaCMR4zUJQQJ99BDACYeBjFXJ3w3AAAFACOGki3V'
endpoint = 'https://vellan.cognitiveservices.azure.com/'
read_url = endpoint + "vision/v3.2/read/analyze"

@app.route('/extract-text', methods=['POST'])
def extract_text():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400
    
    image = request.files['image']
    
    # Read the image data once and store it
    image_data = image.read()
    
    # Send image to Azure Read API
    headers = {
        "Ocp-Apim-Subscription-Key": subscription_key,
        "Content-Type": "application/octet-stream"
    }
    
    response = requests.post(read_url, headers=headers, data=image_data)
    
    if response.status_code != 202:
        return jsonify({'error': 'Azure Read API call failed', 'details': response.text}), 500
    
    operation_url = response.headers["Operation-Location"]
    
    # Polling for result
    while True:
        result = requests.get(operation_url, headers={"Ocp-Apim-Subscription-Key": subscription_key}).json()
        if result["status"] in ["succeeded", "failed"]:
            break
        time.sleep(1)
    
    if result["status"] == "succeeded":
        extracted_text = []
        for line in result["analyzeResult"]["readResults"][0]["lines"]:
            # Create a dictionary for each line
            line_data = {
                "text": line["text"],
                "boundingBox": convert_bbox_format(line["boundingBox"]),  # Convert to 4-point format
                "confidence": None  # Default to None
            }
            
            # Azure's OCR API returns word-level confidence, so we can calculate the average
            if "words" in line and line["words"]:
                confidences = [word.get("confidence", 0) for word in line["words"] if "confidence" in word]
                if confidences:
                    line_data["confidence"] = sum(confidences) / len(confidences)
            
            extracted_text.append(line_data)
        
        return jsonify({
            'extracted_text': extracted_text
        })
    else:
        return jsonify({'error': 'Text recognition failed'}), 500


def convert_bbox_format(bounding_box):
    """
    Convert 8-point bounding box (from Azure) into 4-point (top-left, bottom-right).
    """
    x_coords = bounding_box[::2]
    y_coords = bounding_box[1::2]
    x0, y0 = min(x_coords), min(y_coords)
    x1, y1 = max(x_coords), max(y_coords)

    # Return as [x_min, y_min, x_max, y_max]
    return [x0, y0, x1, y1]


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
