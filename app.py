from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, jsonify
import os
import time
import datetime
import logging
import requests
import tempfile
import json
import uuid

app = Flask(__name__)
app.secret_key = "pdf_intelligence_system_key"  # For flash messages

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Determine if running in Azure
is_azure = os.environ.get('WEBSITE_SITE_NAME') is not None

# Set up paths differently based on environment
if is_azure:
    # Azure paths
    base_dir = os.environ.get('HOME', '')
    UPLOAD_FOLDER = os.path.join(base_dir, 'site', 'wwwroot', 'uploads')
    OUTPUT_FOLDER = os.path.join(base_dir, 'site', 'wwwroot', 'output')
else:
    # Local development paths
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    OUTPUT_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit

# OCR.space API configuration
# Register for a free API key at https://ocr.space/ocrapi/freekey
OCR_API_KEY = os.environ.get('OCR_API_KEY', 'K81878397188957')  # Default to a placeholder key
OCR_API_URL = 'https://api.ocr.space/parse/image'

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_with_ocr_space(file_path):
    """
    Extract text from a PDF or image file using OCR.space API
    """
    try:
        # Prepare the payload for OCR.space API
        payload = {
            'isOverlayRequired': False,
            'apikey': OCR_API_KEY,
            'language': 'eng',  # Default language English
            'isCreateSearchablePdf': False,
            'isSearchablePdfHideTextLayer': False,
        }
        
        # For PDF files
        if file_path.lower().endswith('.pdf'):
            payload['isTable'] = True  # Better extraction for tables in PDFs
            payload['detectOrientation'] = True  # Auto-detect text orientation

        # Create file object
        with open(file_path, 'rb') as f:
            files = {'file': f}
            
            # Make the API request
            logger.info(f"Sending file {file_path} to OCR.space API")
            response = requests.post(OCR_API_URL, files=files, data=payload)
            
            # Check if the request was successful
            if response.status_code == 200:
                result = response.json()
                
                # Check if OCR was successful
                if result['OCRExitCode'] == 1:  # 1 means success
                    extracted_text = ""
                    for page in result['ParsedResults']:
                        extracted_text += page['ParsedText'] + "\n\n"
                    
                    return {
                        'success': True,
                        'text': extracted_text,
                        'exit_code': result['OCRExitCode'],
                        'process_time': result.get('ProcessingTimeInMilliseconds', 0) / 1000,
                        'pages_processed': len(result['ParsedResults'])
                    }
                else:
                    error_message = result.get('ErrorMessage', ['Unknown error'])[0]
                    return {
                        'success': False,
                        'error': f"OCR Error: {error_message}",
                        'exit_code': result['OCRExitCode']
                    }
            else:
                return {
                    'success': False,
                    'error': f"HTTP Error: {response.status_code} - {response.text}",
                    'exit_code': -1
                }
    except Exception as e:
        logger.error(f"Error in OCR API call: {str(e)}")
        return {
            'success': False,
            'error': f"Exception: {str(e)}",
            'exit_code': -1
        }

def process_file(file_path):
    """
    Process a PDF file using OCR.space API and save the results
    """
    filename = os.path.basename(file_path)
    base_name = os.path.splitext(filename)[0]
    output_text_path = os.path.join(app.config['OUTPUT_FOLDER'], f"{base_name}.txt")
    output_md_path = os.path.join(app.config['OUTPUT_FOLDER'], f"{base_name}.md")
    output_json_path = os.path.join(app.config['OUTPUT_FOLDER'], f"{base_name}.json")
    
    # Call OCR.space API
    ocr_result = extract_text_with_ocr_space(file_path)
    
    # Save the results
    if ocr_result['success']:
        # Save plain text
        with open(output_text_path, 'w', encoding='utf-8') as f:
            f.write(ocr_result['text'])
        
        # Save markdown
        with open(output_md_path, 'w', encoding='utf-8') as f:
            f.write(f"# Text Extraction Results: {base_name}\n\n")
            f.write(f"## Overview\n\n")
            f.write(f"This document contains text extracted from `{filename}` using OCR.space API.\n\n")
            f.write(f"- Processing time: {ocr_result['process_time']} seconds\n")
            f.write(f"- Pages processed: {ocr_result['pages_processed']}\n\n")
            f.write("## Extracted Content\n\n")
            f.write("```\n")
            f.write(ocr_result['text'])
            f.write("\n```\n\n")
            f.write(f"*Generated at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
        
        # Save JSON result
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump({
                'filename': filename,
                'processing_time': ocr_result['process_time'],
                'pages_processed': ocr_result['pages_processed'],
                'extracted_text': ocr_result['text'],
                'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }, f, indent=2)
        
        return {
            'success': True,
            'text_path': output_text_path,
            'md_path': output_md_path,
            'json_path': output_json_path,
            'text': ocr_result['text'][:500] + '...' if len(ocr_result['text']) > 500 else ocr_result['text']
        }
    else:
        # In case of error, save the error info
        with open(output_text_path, 'w', encoding='utf-8') as f:
            f.write(f"Error extracting text from {filename}\n\n")
            f.write(f"Error details: {ocr_result['error']}\n")
        
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump({
                'filename': filename,
                'success': False,
                'error': ocr_result['error'],
                'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }, f, indent=2)
        
        return {
            'success': False,
            'error': ocr_result['error'],
            'text_path': output_text_path,
            'json_path': output_json_path
        }

@app.route('/')
def home():
    """Home page with information about the PDF Intelligence System"""
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    """Handle file uploads and processing"""
    if request.method == 'POST':
        # Check if a file was submitted
        if 'file' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        
        # Check if a file was selected
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)
        
        # Check if the file has an allowed extension
        if file and allowed_file(file.filename):
            # Generate a unique filename to prevent collisions
            original_filename = file.filename
            filename = f"{uuid.uuid4().hex}_{original_filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Save the uploaded file
            file.save(file_path)
            
            try:
                # Process the file with OCR
                result = process_file(file_path)
                
                if result['success']:
                    flash(f'File successfully uploaded and processed: {original_filename}', 'success')
                else:
                    flash(f'Error processing file: {result["error"]}', 'error')
                
                return redirect(url_for('upload_file'))
            except Exception as e:
                logger.error(f"Error processing file {filename}: {str(e)}")
                flash(f'Error processing file: {str(e)}', 'error')
                return redirect(request.url)
        else:
            allowed_extensions = ', '.join(ALLOWED_EXTENSIONS)
            flash(f'Only {allowed_extensions} files are allowed', 'error')
            return redirect(request.url)
    
    # Get list of uploaded files safely
    try:
        uploaded_files = []
        for f in os.listdir(app.config['UPLOAD_FOLDER']):
            if any(f.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS):
                # Extract original filename from UUID_filename pattern
                if '_' in f:
                    display_name = '_'.join(f.split('_')[1:])
                else:
                    display_name = f
                uploaded_files.append({'filename': f, 'display_name': display_name})
    except Exception as e:
        logger.error(f"Error listing upload folder: {str(e)}")
        uploaded_files = []
    
    processed_files = []
    
    # Group output files with their corresponding uploaded files
    for file_info in uploaded_files:
        f = file_info['filename']
        base_name = os.path.splitext(f)[0]
        outputs = []
        
        text_path = os.path.join(app.config['OUTPUT_FOLDER'], f"{base_name}.txt")
        md_path = os.path.join(app.config['OUTPUT_FOLDER'], f"{base_name}.md")
        json_path = os.path.join(app.config['OUTPUT_FOLDER'], f"{base_name}.json")
        
        if os.path.exists(text_path):
            outputs.append({'type': 'Text', 'filename': f"{base_name}.txt"})
        
        if os.path.exists(md_path):
            outputs.append({'type': 'Markdown', 'filename': f"{base_name}.md"})
        
        if os.path.exists(json_path):
            outputs.append({'type': 'JSON', 'filename': f"{base_name}.json"})
        
        if outputs:
            processed_files.append({
                'pdf': file_info['display_name'],
                'filename': f,
                'outputs': outputs
            })
    
    return render_template('upload.html', 
                          uploaded_files=uploaded_files,
                          processed_files=processed_files)

@app.route('/download/<filename>')
def download_file(filename):
    """Download a file from the output folder"""
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename, as_attachment=True)

@app.route('/delete/<filename>')
def delete_file(filename):
    """Delete a file and its associated output files"""
    try:
        # Delete the uploaded file
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Delete associated output files
        base_name = os.path.splitext(filename)[0]
        text_path = os.path.join(app.config['OUTPUT_FOLDER'], f"{base_name}.txt")
        md_path = os.path.join(app.config['OUTPUT_FOLDER'], f"{base_name}.md")
        json_path = os.path.join(app.config['OUTPUT_FOLDER'], f"{base_name}.json")
        
        for path in [text_path, md_path, json_path]:
            if os.path.exists(path):
                os.remove(path)
        
        flash(f'File deleted: {filename}', 'success')
    except Exception as e:
        flash(f'Error deleting file: {str(e)}', 'error')
    
    return redirect(url_for('upload_file'))

@app.route('/status')
def status():
    """Display system status and diagnostics"""
    # Get system information safely
    try:
        uploaded_files_count = len([f for f in os.listdir(UPLOAD_FOLDER) 
                                  if any(f.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS)])
    except Exception:
        uploaded_files_count = 0
        
    try:
        processed_files_count = len([f for f in os.listdir(OUTPUT_FOLDER) 
                                    if f.endswith('.txt')])
    except Exception:
        processed_files_count = 0
    
    # Test OCR API (without sending a file)
    ocr_api_status = "Unknown"
    try:
        response = requests.get('https://api.ocr.space/status')
        if response.status_code == 200:
            ocr_api_status = "Available"
        else:
            ocr_api_status = f"Error: {response.status_code}"
    except Exception as e:
        ocr_api_status = f"Error: {str(e)}"
    
    system_info = {
        'python_version': os.environ.get('PYTHON_VERSION', 'Unknown'),
        'upload_folder': UPLOAD_FOLDER,
        'output_folder': OUTPUT_FOLDER,
        'uploaded_files': uploaded_files_count,
        'processed_files': processed_files_count,
        'server_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'environment': 'Azure' if is_azure else 'Local Development',
        'ocr_api_status': ocr_api_status,
        'ocr_api_key_set': 'Yes' if OCR_API_KEY != 'K81878397188957' else 'Using Demo Key'
    }
    
    return render_template('status.html', system_info=system_info)

@app.route('/api/ocr', methods=['POST'])
def api_ocr():
    """API endpoint for OCR processing"""
    # Check if a file was submitted
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file part'}), 400
    
    file = request.files['file']
    
    # Check if a file was selected
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    # Check if the file has an allowed extension
    if file and allowed_file(file.filename):
        # Save to a temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        file.save(temp_file.name)
        temp_file.close()
        
        try:
            # Process with OCR.space
            result = extract_text_with_ocr_space(temp_file.name)
            
            # Remove temporary file
            os.unlink(temp_file.name)
            
            if result['success']:
                return jsonify({
                    'success': True,
                    'text': result['text'],
                    'pages_processed': result['pages_processed'],
                    'processing_time': result['process_time']
                })
            else:
                return jsonify({
                    'success': False,
                    'error': result['error']
                }), 400
        except Exception as e:
            # Remove temporary file
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
            
            logger.error(f"API error: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500
    else:
        allowed_extensions = ', '.join(ALLOWED_EXTENSIONS)
        return jsonify({'success': False, 'error': f'Only {allowed_extensions} files are allowed'}), 400

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000) 