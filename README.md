# Bill Scanning System - Tally to Google Sheets

A mobile-based bill scanning system that extracts structured data from Tally bills using OCR and automatically stores the extracted values in Google Sheets.

## Features

- **Mobile-Friendly**: Capture bills using phone camera
- **OCR Processing**: Extract text using Google Cloud Vision API or Tesseract
- **Smart Parsing**: Automatically identifies and extracts bill fields
- **Data Validation**: Validates extracted data for accuracy
- **Google Sheets Integration**: Automatically appends data to spreadsheet
- **REST API**: Easy-to-use endpoints for mobile apps

## Extracted Fields

The system extracts the following fields from Tally bills:

- **Buyer** (Store/Party Name)
- **Total Before Tax** (Taxable Value)
- **CGST** (Central GST Amount)
- **SGST** (State GST/UTGST Amount)
- **Grand Total** (Total with Tax)

## Architecture

```
Mobile App (Camera)
      ↓
   [Image Upload]
      ↓
Flask API Server
      ↓
   ┌──────────┐
   │   OCR    │ → Extract Text
   └──────────┘
      ↓
   ┌──────────┐
   │  Parser  │ → Extract Fields
   └──────────┘
      ↓
   ┌──────────┐
   │ Validator│ → Validate Data
   └──────────┘
      ↓
   ┌──────────┐
   │  Sheets  │ → Save to Google Sheets
   └──────────┘
```

## Installation

### Prerequisites

- Python 3.8 or higher
- Google Cloud account (for Vision API) OR Tesseract OCR
- Google Service Account (for Sheets API)

### Step 1: Clone and Install Dependencies

```bash
cd /home/janvi/JAVA
pip install -r requirements.txt
```

### Step 2: Set Up Google Cloud Vision API (Option 1 - Recommended)

1. **Create a Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project

2. **Enable Vision API**
   - Navigate to "APIs & Services" > "Library"
   - Search for "Cloud Vision API"
   - Click "Enable"

3. **Create Service Account**
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "Service Account"
   - Download the JSON key file
   - Save as `credentials.json` in the project directory

### Step 2 (Alternative): Set Up Tesseract OCR (Option 2 - Free, Local)

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install tesseract-ocr

# MacOS
brew install tesseract

# Install Python package
pip install pytesseract
```

### Step 3: Set Up Google Sheets API

1. **Enable Google Sheets API**
   - In the same Google Cloud project
   - Navigate to "APIs & Services" > "Library"
   - Search for "Google Sheets API"
   - Click "Enable"

2. **Use Same Service Account or Create New One**
   - Use the same service account from Vision API
   - OR create a new one following the same steps
   - Download JSON key as `sheets_credentials.json`

3. **Create Google Spreadsheet**
   - Go to [Google Sheets](https://sheets.google.com)
   - Create a new spreadsheet
   - Share it with the service account email (found in JSON file)
     - Give "Editor" permissions
   - Copy the Spreadsheet ID from the URL:
     ```
     https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit
     ```

### Step 4: Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env file with your values
nano .env
```

Update the following values:
```env
GOOGLE_APPLICATION_CREDENTIALS=credentials.json
GOOGLE_SHEETS_CREDENTIALS=sheets_credentials.json
SPREADSHEET_ID=your_actual_spreadsheet_id_here
SHEET_NAME=Bills
```

## Usage

### Running the API Server

```bash
python app.py
```

The server will start on `http://0.0.0.0:5000`

### Testing Locally

Test with sample bill images:

```bash
# Test with Google Vision API
python test_local.py --google

# Test with Tesseract OCR
python test_local.py --tesseract

# Auto-detect available OCR
python test_local.py
```

### API Endpoints

#### 1. Health Check
```bash
GET /health
```

#### 2. Scan Bill (Extract Only - No Save)
```bash
POST /api/scan-bill
Content-Type: multipart/form-data

Body:
  image: [file]
```

**Response:**
```json
{
  "success": true,
  "data": {
    "buyer": "Manal Super Market",
    "total_before_tax": 14399.74,
    "cgst": 402.42,
    "sgst": 402.42,
    "grand_total": 15204.58
  },
  "validation": {
    "is_valid": true,
    "errors": []
  }
}
```

#### 3. Process Bill (Extract + Save to Sheets)
```bash
POST /api/process-bill
Content-Type: multipart/form-data

Body:
  image: [file]
```

**Response:**
```json
{
  "success": true,
  "message": "Bill processed and saved successfully",
  "data": {
    "buyer": "Manal Super Market",
    "total_before_tax": 14399.74,
    "cgst": 402.42,
    "sgst": 402.42,
    "grand_total": 15204.58
  },
  "sheets_result": {
    "success": true,
    "row_number": 42
  }
}
```

#### 4. Get All Bills
```bash
GET /api/bills
```

#### 5. Test Google Sheets Connection
```bash
GET /api/test-connection
```

### Using with cURL

```bash
# Scan a bill
curl -X POST http://localhost:5000/api/scan-bill \
  -F "image=@photos/1.jpeg"

# Process and save to sheets
curl -X POST http://localhost:5000/api/process-bill \
  -F "image=@photos/1.jpeg"
```

### Mobile App Integration

#### Android (Kotlin)
```kotlin
val client = OkHttpClient()
val file = File("path/to/image.jpg")

val requestBody = MultipartBody.Builder()
    .setType(MultipartBody.FORM)
    .addFormDataPart("image", file.name,
        RequestBody.create(MediaType.parse("image/jpeg"), file))
    .build()

val request = Request.Builder()
    .url("http://your-server:5000/api/process-bill")
    .post(requestBody)
    .build()

client.newCall(request).execute()
```

#### iOS (Swift)
```swift
let url = URL(string: "http://your-server:5000/api/process-bill")!
var request = URLRequest(url: url)
request.httpMethod = "POST"

let boundary = UUID().uuidString
request.setValue("multipart/form-data; boundary=\(boundary)",
                 forHTTPHeaderField: "Content-Type")

// Add image data to request body
// ... (implement multipart form data)

URLSession.shared.dataTask(with: request) { data, response, error in
    // Handle response
}.resume()
```

## Project Structure

```
/home/janvi/JAVA/
│
├── app.py                    # Flask API server
├── ocr_extractor.py          # OCR text extraction module
├── bill_parser.py            # Bill data parsing logic
├── sheets_integration.py     # Google Sheets integration
├── config.py                 # Configuration settings
├── test_local.py             # Local testing script
│
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variables template
├── .env                      # Your environment variables (create this)
│
├── credentials.json          # Google Vision API credentials (create this)
├── sheets_credentials.json   # Google Sheets API credentials (create this)
│
├── photos/                   # Sample bill images
│   ├── 1.jpeg
│   ├── 2.jpeg
│   └── ...
│
└── uploads/                  # Temporary uploaded images (auto-created)
```

## Troubleshooting

### OCR Issues

**Problem**: No text extracted from image

**Solutions**:
- Ensure image is clear and well-lit
- Check if OCR credentials are configured correctly
- Try with Tesseract as fallback
- Verify image format is supported

### Google Sheets Issues

**Problem**: "Permission denied" or "Spreadsheet not found"

**Solutions**:
- Verify spreadsheet is shared with service account email
- Check if Spreadsheet ID is correct in `.env`
- Ensure Google Sheets API is enabled in Google Cloud Console
- Verify service account has "Editor" permissions

### Parsing Issues

**Problem**: Some fields not extracted correctly

**Solutions**:
- Check if bill format matches Tally standard format
- Review `bill_parser.py` regex patterns
- Enable debug mode to see extracted text
- Manually review OCR output

## Performance

- **OCR Processing**: 2-5 seconds per image
- **Parsing**: < 100ms
- **Google Sheets API**: 500ms - 1s
- **Total**: 3-7 seconds per bill

## Security Considerations

1. **API Keys**: Never commit credentials to git
   ```bash
   # Add to .gitignore
   echo "credentials.json" >> .gitignore
   echo "sheets_credentials.json" >> .gitignore
   echo ".env" >> .gitignore
   ```

2. **File Uploads**: File size limited to 16MB
3. **CORS**: Configure CORS properly for production
4. **HTTPS**: Use HTTPS in production
5. **Rate Limiting**: Implement rate limiting for production

## Deployment

### Deploy to Cloud (Google Cloud Run Example)

```bash
# 1. Create Dockerfile
# 2. Build container
docker build -t bill-scanner .

# 3. Push to registry
docker tag bill-scanner gcr.io/YOUR_PROJECT/bill-scanner
docker push gcr.io/YOUR_PROJECT/bill-scanner

# 4. Deploy to Cloud Run
gcloud run deploy bill-scanner \
  --image gcr.io/YOUR_PROJECT/bill-scanner \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### Deploy to Heroku

```bash
# 1. Create Procfile
echo "web: python app.py" > Procfile

# 2. Deploy
heroku create your-app-name
git push heroku main
```

## Future Enhancements

- [ ] Support for multiple invoice formats (not just Tally)
- [ ] Batch processing of multiple bills
- [ ] Database integration for bill history
- [ ] User authentication and multi-user support
- [ ] Mobile app (React Native / Flutter)
- [ ] PDF support
- [ ] Email integration (process bills from email)
- [ ] Dashboard for analytics
- [ ] Export to multiple formats (CSV, Excel, PDF)

## License

MIT License

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review sample images in `photos/` directory
3. Run `python test_local.py` to diagnose issues
4. Check logs for detailed error messages

## Credits

- Google Cloud Vision API for OCR
- Tesseract OCR for open-source alternative
- gspread for Google Sheets integration
- Flask for web framework
