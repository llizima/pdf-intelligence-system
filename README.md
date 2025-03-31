# PDF Intelligence System with OCR

This application provides a web-based interface for extracting text from PDF documents and images using OCR (Optical Character Recognition) technology. It leverages the OCR.space API to process documents and provides the extracted text in multiple formats.

## Live Demo
A demo version of this application is available at: https://pdf-web-app-dev.azurewebsites.net

## Features

- Upload and process PDF documents and images (PDF, JPG, JPEG, PNG)
- Extract text using the OCR.space API
- Generate outputs in multiple formats (text, markdown, JSON)
- RESTful API for integration with other applications
- System status and diagnostics page
- Responsive, modern user interface

## Architecture

The application is built using Flask and is designed to run on Azure Web App. It uses:

- **Flask**: Web framework for handling HTTP requests
- **OCR.space API**: For Optical Character Recognition of documents
- **Bootstrap 5**: For the responsive user interface
- **Azure Web App**: For hosting the application

## Deployment

### Prerequisites

- Azure CLI installed and configured
- An Azure subscription
- An existing Azure Web App (Python 3.9) 

### Deployment Steps

1. Clone this repository or download the source code
2. Run the deployment script from the root directory:

```powershell
./deploy_ocr_app.ps1
```

This script will:
- Validate all required files
- Create a deployment package (zip file)
- Deploy the application to your Azure Web App
- Optionally set an OCR.space API key as an environment variable

### Manual Deployment

If you prefer to deploy manually:

1. Zip the contents of the `pdf_app_ocr` directory
2. Deploy using Azure CLI:

```bash
az webapp deploy --resource-group YOUR_RESOURCE_GROUP --name YOUR_WEB_APP_NAME --src-path YOUR_ZIP_FILE --type zip
```

## Configuration

### OCR.space API Key

The application uses a demo OCR.space API key by default. For production use, it's recommended to get your own API key from [OCR.space](https://ocr.space/ocrapi/freekey).

You can set the API key as an environment variable in Azure:

```bash
az webapp config appsettings set --resource-group YOUR_RESOURCE_GROUP --name YOUR_WEB_APP_NAME --settings "OCR_API_KEY=YOUR_API_KEY"
```

## Local Development

To run the application locally:

1. Create a Python virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the application:

```bash
python app.py
```

The application will be available at `http://localhost:8000`.

## API Usage

### Endpoint

```
POST /api/ocr
```

### Request

Send a multipart/form-data request with the file to process in the "file" field.

### Example (cURL)

```bash
curl -X POST -F "file=@document.pdf" https://your-app-name.azurewebsites.net/api/ocr
```

### Example (Python)

```python
import requests

url = "https://your-app-name.azurewebsites.net/api/ocr"
files = {"file": open("document.pdf", "rb")}
response = requests.post(url, files=files)

if response.status_code == 200:
    result = response.json()
    print(f"Extracted text: {result['text']}")
    print(f"Pages processed: {result['pages_processed']}")
    print(f"Processing time: {result['processing_time']} seconds")
else:
    print(f"Error: {response.status_code} - {response.text}")
```

### Response (Success)

```json
{
  "success": true,
  "text": "Extracted text content...",
  "pages_processed": 1,
  "processing_time": 2.345
}
```

### Response (Error)

```json
{
  "success": false,
  "error": "Error message details"
}
```

## License

This project is open-source and available under the MIT License.

## Credits

- OCR processing powered by [OCR.space](https://ocr.space/)
- UI built with [Bootstrap 5](https://getbootstrap.com/)
- Server-side framework: [Flask](https://flask.palletsprojects.com/) 