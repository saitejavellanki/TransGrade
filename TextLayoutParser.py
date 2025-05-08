from flask import Flask, request, jsonify, render_template_string, redirect, url_for
import os
import json
import time
import uuid
import re  # Import re at the top of the file
import traceback

# Import Azure modules
# You need to install these with: pip install azure-ai-formrecognizer
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient

app = Flask(__name__)

# Azure Form Recognizer Configuration
# Replace these with your actual Form Recognizer endpoint and key
# Consider using environment variables for these sensitive values
FORM_RECOGNIZER_ENDPOINT = 'https://test1tran.cognitiveservices.azure.com/'
FORM_RECOGNIZER_KEY = 'W9FBaeGXDDqNVqUz7W9yEO6NoGxQElZA6BR63yWYhaA0IueHqWjqJQQJ99BEACYeBjFXJ3w3AAALACOGHJy1'

# Create a directory to store uploaded files
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Azure Form Recognizer Document Analysis</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f0f2f5;
            color: #333;
        }
        .container {
            max-width: 1000px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #0078d4;
            margin-top: 0;
        }
        h2 {
            color: #0078d4;
            margin-top: 30px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: 500;
        }
        input[type="file"] {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        .button {
            background-color: #0078d4;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
            transition: background-color 0.3s;
        }
        .button:hover {
            background-color: #005a9e;
        }
        .result-container {
            margin-top: 30px;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 20px;
            background-color: #f9f9f9;
        }
        .result-tabs {
            display: flex;
            border-bottom: 1px solid #ddd;
            margin-bottom: 15px;
        }
        .tab {
            padding: 10px 20px;
            cursor: pointer;
            background-color: #f1f1f1;
            border: 1px solid #ddd;
            border-bottom: none;
            margin-right: 5px;
            border-radius: 4px 4px 0 0;
        }
        .tab.active {
            background-color: white;
            border-bottom: 1px solid white;
            margin-bottom: -1px;
        }
        .tab-content {
            display: none;
            padding: 15px;
            border: 1px solid #ddd;
            border-top: none;
            background-color: white;
        }
        .tab-content.active {
            display: block;
        }
        pre {
            white-space: pre-wrap;
            background-color: #f5f5f5;
            padding: 10px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            overflow: auto;
            max-height: 500px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        th {
            background-color: #f2f2f2;
        }
        .status {
            padding: 10px;
            margin: 10px 0;
            border-radius: 4px;
        }
        .status.success {
            background-color: #e6ffed;
            border: 1px solid #b4d9b7;
            color: #1e7830;
        }
        .status.error {
            background-color: #ffeef0;
            border: 1px solid #f1b7c0;
            color: #d73a49;
        }
        .status.info {
            background-color: #f1f8ff;
            border: 1px solid #c9e2f9;
            color: #0366d6;
        }
        .table-view {
            border: 1px solid #ddd;
            margin-top: 15px;
        }
        .example-json {
            padding: 10px;
            background-color: #f8f8f8;
            border: 1px solid #ddd;
            font-size: 12px;
        }
        .toggle-btn {
            background-color: #f1f1f1;
            border: 1px solid #ddd;
            padding: 5px 10px;
            cursor: pointer;
            font-size: 14px;
        }
        .or-divider {
            display: flex;
            align-items: center;
            margin: 20px 0;
        }
        .or-divider:before, .or-divider:after {
            content: "";
            flex-grow: 1;
            height: 1px;
            background-color: #ddd;
            margin: 0 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Azure Form Recognizer Document Analysis</h1>
        
        {% if error %}
        <div class="status error">
            <strong>Error:</strong> {{ error }}
        </div>
        {% endif %}
        
        {% if success_message %}
        <div class="status success">
            {{ success_message }}
        </div>
        {% endif %}
        
        <div class="form-group">
            <h2>Upload Document Image</h2>
            <p>Upload an image or PDF document to analyze with Azure Form Recognizer.</p>
            <form action="/upload" method="POST" enctype="multipart/form-data">
                <input type="file" name="document" accept=".jpg,.jpeg,.png,.pdf,.tiff" required>
                <p>Supported formats: JPG, JPEG, PNG, PDF, TIFF</p>
                <button type="submit" class="button">Analyze Document</button>
            </form>
        </div>
        
        <div class="or-divider">OR</div>
        
        <div class="form-group">
            <h2>Use Existing OCR Data</h2>
            <p>Paste your existing OCR JSON data to enhance with Form Recognizer's layout understanding.</p>
            <form action="/process_json" method="POST">
                <textarea name="ocrJson" rows="10" style="width: 100%; padding: 10px;" placeholder="Paste your OCR JSON data here..."></textarea>
                <p>Example format:</p>
                <div class="example-json">
                    <button class="toggle-btn" onclick="toggleJsonExample()">Show/Hide Example</button>
                    <pre id="json-example" style="display: none;">
{
    "extracted_text": [
        {
            "boundingBox": [27, 15, 43, 13, 44, 29, 29, 31],
            "confidence": 0.953,
            "text": "I"
        },
        {
            "boundingBox": [34, 42, 525, 22, 526, 42, 34, 64],
            "confidence": 0.842,
            "text": "1. A) Everything avaliable in our environment"
        }
    ]
}
                    </pre>
                </div>
                <button type="submit" class="button">Process OCR Data</button>
            </form>
        </div>
        
        {% if results %}
        <h2>Analysis Results</h2>
        <div class="result-container">
            <div class="result-tabs">
                <div class="tab active" onclick="showTab('structured')">Structured Content</div>
                <div class="tab" onclick="showTab('tables')">Tables</div>
                <div class="tab" onclick="showTab('paragraphs')">Paragraphs</div>
                <div class="tab" onclick="showTab('json')">Raw JSON</div>
            </div>
            
            <div id="structured" class="tab-content active">
                <h3>Document Structure</h3>
                {% if results.document %}
                <ul>
                    {% for item in results.document %}
                    <li>
                        <strong>{{ item.type }}:</strong> {{ item.content }}
                        {% if item.items and item.items is iterable %}
                        <ul>
                            {% for subitem in item.items %}
                            <li>{{ subitem }}</li>
                            {% endfor %}
                        </ul>
                        {% endif %}
                    </li>
                    {% endfor %}
                </ul>
                {% else %}
                <p>No structured content found</p>
                {% endif %}
            </div>
            
            <div id="tables" class="tab-content">
                <h3>Detected Tables</h3>
                {% if results.tables and results.tables is mapping %}
                {% for table_idx, table in results.tables.items() %}
                {% if table is iterable %}
                <h4>Table {{ table_idx }}</h4>
                <div class="table-view">
                    <table>
                        {% for row in table %}
                        {% if row is iterable %}
                        <tr>
                            {% for cell in row %}
                            <td>{{ cell }}</td>
                            {% endfor %}
                        </tr>
                        {% endif %}
                        {% endfor %}
                    </table>
                </div>
                {% endif %}
                {% endfor %}
                {% else %}
                <p>No tables detected in the document</p>
                {% endif %}
            </div>
            
            <div id="paragraphs" class="tab-content">
                <h3>Detected Paragraphs</h3>
                {% if results.paragraphs and results.paragraphs is iterable %}
                {% for para in results.paragraphs %}
                <div style="margin-bottom: 15px; padding: 10px; background-color: #f9f9f9; border-left: 3px solid #0078d4;">
                    {{ para }}
                </div>
                {% endfor %}
                {% else %}
                <p>No paragraphs detected</p>
                {% endif %}
            </div>
            
            <div id="json" class="tab-content">
                <h3>Raw JSON Response</h3>
                <pre>{{ results.raw_json }}</pre>
            </div>
        </div>
        {% endif %}
    </div>
    
    <script>
        function showTab(tabName) {
            // Hide all tab contents
            var tabContents = document.getElementsByClassName('tab-content');
            for (var i = 0; i < tabContents.length; i++) {
                tabContents[i].classList.remove('active');
            }
            
            // Show the selected tab content
            document.getElementById(tabName).classList.add('active');
            
            // Update tab buttons
            var tabs = document.getElementsByClassName('tab');
            for (var i = 0; i < tabs.length; i++) {
                tabs[i].classList.remove('active');
            }
            
            // Find and activate the clicked tab
            var tabs = document.getElementsByClassName('tab');
            for (var i = 0; i < tabs.length; i++) {
                if (tabs[i].textContent.toLowerCase().includes(tabName)) {
                    tabs[i].classList.add('active');
                }
            }
        }
        
        function toggleJsonExample() {
            var example = document.getElementById('json-example');
            if (example.style.display === 'none') {
                example.style.display = 'block';
            } else {
                example.style.display = 'none';
            }
        }
    </script>
</body>
</html>
"""

def get_document_analysis_client():
    """Create and return an Azure Form Recognizer Document Analysis client"""
    credential = AzureKeyCredential(FORM_RECOGNIZER_KEY)
    return DocumentAnalysisClient(endpoint=FORM_RECOGNIZER_ENDPOINT, credential=credential)

def analyze_document(file_path):
    """Analyze a document using Azure Form Recognizer"""
    document_analysis_client = get_document_analysis_client()
    
    with open(file_path, "rb") as f:
        poller = document_analysis_client.begin_analyze_document("prebuilt-document", f)
        result = poller.result()
    
    return result

def process_form_recognizer_result(result):
    """Process and structure the Form Recognizer analysis result"""
    processed_result = {
        'raw_json': json.dumps(result.to_dict(), indent=2),
        'document': [],
        'tables': {},
        'paragraphs': []
    }
    
    # Extract tables
    for i, table in enumerate(result.tables):
        table_data = []
        for row_idx in range(table.row_count):
            row_data = []
            for col_idx in range(table.column_count):
                # Find cells for this row and column
                cell_content = ""
                for cell in table.cells:
                    if cell.row_index == row_idx and cell.column_index == col_idx:
                        cell_content = cell.content
                        break
                row_data.append(cell_content)
            table_data.append(row_data)
        processed_result['tables'][i+1] = table_data
    
    # Extract paragraphs
    for paragraph in result.paragraphs:
        processed_result['paragraphs'].append(paragraph.content)
    
    # Create a debug log of the available attributes and their types
    result_dict = result.to_dict()
    print(f"Available keys in result: {list(result_dict.keys())}")
    
    # Approach based on document info found in paragraphs and spans
    current_section = None
    
    # Create sections from paragraphs
    for i, paragraph in enumerate(result.paragraphs):
        content = paragraph.content
        
        # Try to determine if this might be a heading
        is_heading = False
        
        # Check if spans property exists and inspect it for font info 
        if hasattr(paragraph, 'spans') and paragraph.spans:
            for span in paragraph.spans:
                # Look for typical heading markers like larger font or bold text
                if hasattr(span, 'appearance') and hasattr(span.appearance, 'style'):
                    if getattr(span.appearance.style, 'is_bold', False) or getattr(span.appearance.style, 'font_size', 0) > 12:
                        is_heading = True
                        break
        
        # Simple heuristic: short paragraphs that end with a colon are likely headings
        if not is_heading and (i == 0 or (len(content) < 100 and content.strip().endswith(':'))):
            is_heading = True
        
        if is_heading:
            current_section = {
                'type': 'SectionHeading',
                'content': content,
                'items': []
            }
            processed_result['document'].append(current_section)
        elif content.strip().startswith(('-', '•', '*')) or re.match(r'^\d+[\.\)]', content.strip()):
            # This looks like a list item
            if current_section:
                current_section['items'].append(content)
            else:
                # Create a default section if none exists
                current_section = {
                    'type': 'List',
                    'content': 'List items:',
                    'items': [content]
                }
                processed_result['document'].append(current_section)
        else:
            # Regular text paragraph
            paragraph_entry = {
                'type': 'Text',
                'content': content
            }
            processed_result['document'].append(paragraph_entry)
            current_section = None  # Reset current section
    
    # If no document structure was created, create a simple one based on paragraphs
    if not processed_result['document'] and processed_result['paragraphs']:
        for i, para in enumerate(processed_result['paragraphs']):
            processed_result['document'].append({
                'type': 'Paragraph',
                'content': para,
                'items': []
            })
    
    return processed_result

def process_ocr_json(ocr_data):
    """
    Process existing OCR JSON data using Form Recognizer's layout capabilities
    """
    try:
        # Get the extracted_text from the OCR data
        extracted_text = ocr_data.get('extracted_text', [])
        
        # Verify extracted_text is a list before proceeding
        if not isinstance(extracted_text, list):
            raise ValueError("'extracted_text' must be a list")
        
        # Sort by Y coordinate to reconstruct reading order
        sorted_text = sorted(extracted_text, key=lambda x: x['boundingBox'][1])
        
        processed_result = {
            'raw_json': json.dumps(ocr_data, indent=2),
            'document': [],
            'paragraphs': [],
            'tables': {}
        }
        
        # Group text into paragraphs based on Y-coordinates
        current_para = []
        current_y = None
        y_threshold = 20  # Adjust based on document line spacing
        
        for item in sorted_text:
            text = item.get('text', '').strip()
            y_coord = item['boundingBox'][1] if len(item.get('boundingBox', [])) > 1 else 0
            
            if not text:
                continue
                
            if current_y is None or abs(y_coord - current_y) <= y_threshold:
                current_para.append(text)
                current_y = y_coord
            else:
                if current_para:
                    para_text = " ".join(current_para)
                    processed_result['paragraphs'].append(para_text)
                    
                    # Add to document structure
                    if re.match(r'^\d+\.', para_text):
                        processed_result['document'].append({
                            'type': 'Question',
                            'content': para_text,
                            'items': []  # Ensure items is always a list
                        })
                    else:
                        processed_result['document'].append({
                            'type': 'Text',
                            'content': para_text,
                            'items': []  # Ensure items is always a list
                        })
                        
                current_para = [text]
                current_y = y_coord
        
        # Add the last paragraph
        if current_para:
            para_text = " ".join(current_para)
            processed_result['paragraphs'].append(para_text)
            
            if re.match(r'^\d+\.', para_text):
                processed_result['document'].append({
                    'type': 'Question',
                    'content': para_text,
                    'items': []  # Ensure items is always a list
                })
            else:
                processed_result['document'].append({
                    'type': 'Text',
                    'content': para_text,
                    'items': []  # Ensure items is always a list
                })
        
        return processed_result
    except Exception as e:
        error_message = f"Error processing OCR data: {str(e)}"
        tb = traceback.format_exc()
        print(f"{error_message}\n{tb}")
        return {
            'raw_json': json.dumps({"error": str(e), "traceback": tb}),
            'document': [{"type": "Error", "content": error_message, "items": []}],
            'paragraphs': [error_message],
            'tables': {}
        }

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'document' not in request.files:
        return render_template_string(HTML_TEMPLATE, error="No file selected")
    
    file = request.files['document']
    if file.filename == '':
        return render_template_string(HTML_TEMPLATE, error="No file selected")
    
    try:
        # Create a unique filename
        filename = f"{uuid.uuid4()}_{file.filename}"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        
        # Save the file
        file.save(file_path)
        
        # Analyze with Form Recognizer
        result = analyze_document(file_path)
        
        # Process the results
        processed_result = process_form_recognizer_result(result)
        
        # Clean up the file after processing (optional)
        # os.remove(file_path)
        
        return render_template_string(
            HTML_TEMPLATE, 
            results=processed_result,
            success_message=f"Successfully analyzed document: {file.filename}"
        )
    
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Error: {str(e)}\n{error_details}")
        return render_template_string(
            HTML_TEMPLATE, 
            error=f"Error analyzing document: {str(e)}"
        )

@app.route('/process_json', methods=['POST'])
def process_json():
    if 'ocrJson' not in request.form or not request.form['ocrJson'].strip():
        return render_template_string(HTML_TEMPLATE, error="No OCR JSON data provided")
    
    try:
        ocr_json_text = request.form['ocrJson']
        ocr_data = json.loads(ocr_json_text)
        processed_result = process_ocr_json(ocr_data)
        
        return render_template_string(
            HTML_TEMPLATE, 
            results=processed_result,
            success_message="Successfully processed OCR JSON data"
        )
    
    except json.JSONDecodeError as e:
        error_details = traceback.format_exc()
        print(f"JSON Error: {str(e)}\n{error_details}")
        return render_template_string(HTML_TEMPLATE, error=f"Invalid JSON format. Please check your input data: {str(e)}")
    
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Processing Error: {str(e)}\n{error_details}")
        return render_template_string(HTML_TEMPLATE, error=f"Error processing OCR data: {str(e)}")

if __name__ == '__main__':
    app.run(debug=True, port=5001)