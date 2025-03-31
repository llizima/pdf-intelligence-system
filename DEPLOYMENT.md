# Deployment Guide for Azure Web App

This guide explains how to deploy the PDF Intelligence System to Azure Web App.

## Prerequisites

1. Azure CLI installed
2. Azure subscription
3. Azure Web App created with Python 3.9 runtime stack

## Deployment Steps

1. **Set up Azure Web App**
   ```bash
   # Create resource group (if not exists)
   az group create --name pdf-web-rg --location eastus

   # Create App Service plan
   az appservice plan create --name pdf-web-plan --resource-group pdf-web-rg --sku B1 --is-linux

   # Create Web App
   az webapp create --resource-group pdf-web-rg --plan pdf-web-plan --name pdf-web-app-dev --runtime "PYTHON:3.9"
   ```

2. **Configure Environment Variables**
   - Go to Azure Portal > Your Web App > Configuration
   - Add the following application settings:
     - `OCR_SPACE_API_KEY`: Your OCR.space API key
     - `FLASK_APP`: app.py
     - `FLASK_ENV`: production

3. **Deploy the Application**
   ```bash
   # Create deployment package
   Compress-Archive -Path app.py,requirements.txt,templates/* -DestinationPath deploy.zip -Force

   # Deploy to Azure
   az webapp deploy --resource-group pdf-web-rg --name pdf-web-app-dev --src-path deploy.zip --type zip
   ```

4. **Verify Deployment**
   - Visit https://pdf-web-app-dev.azurewebsites.net
   - Check the application logs in Azure Portal if needed

## Troubleshooting

1. **Application Not Starting**
   - Check the application logs in Azure Portal
   - Verify all environment variables are set correctly
   - Ensure requirements.txt is properly formatted

2. **File Upload Issues**
   - Verify the uploads directory exists and has proper permissions
   - Check the MAX_CONTENT_LENGTH setting

3. **OCR Processing Issues**
   - Verify the OCR_SPACE_API_KEY is valid
   - Check the OCR.space API status

## Security Notes

- Never commit sensitive credentials to the repository
- Use Azure Key Vault for storing sensitive information
- Keep your Azure credentials secure
- Regularly rotate API keys and secrets 