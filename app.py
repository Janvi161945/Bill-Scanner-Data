"""
Flask API for Mobile Bill Scanning System
"""
import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import config
from ocr_extractor import OCRExtractor, TesseractOCRExtractor
from bill_parser import BillParser
from sheets_integration import GoogleSheetsIntegration

app = Flask(__name__)
CORS(app)  # Enable CORS for mobile apps

# Configuration
app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH
app.config['UPLOAD_FOLDER'] = config.UPLOAD_FOLDER

# Create upload folder if it doesn't exist
os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)

# Initialize components
try:
    ocr_extractor = OCRExtractor()
    use_google_vision = True
except Exception as e:
    print(f"Google Vision API not available: {e}")
    print("Falling back to Tesseract OCR")
    try:
        ocr_extractor = TesseractOCRExtractor()
        use_google_vision = False
    except Exception as e:
        print(f"Tesseract OCR also not available: {e}")
        ocr_extractor = None

bill_parser = BillParser()


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in config.ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """API root endpoint"""
    return jsonify({
        'service': 'Bill Scanning System',
        'version': '1.0',
        'status': 'active',
        'ocr_engine': 'Google Vision API' if use_google_vision else 'Tesseract OCR',
        'mobile_interface': '/mobile_test.html',
        'endpoints': {
            'health': '/health',
            'scan_bill': '/api/scan-bill (POST)',
            'process_bill': '/api/process-bill (POST)',
            'test_connection': '/api/test-connection (GET)',
            'get_bills': '/api/bills (GET)'
        }
    })


@app.route('/mobile_test.html')
def mobile_test():
    """Serve the mobile test interface"""
    return send_from_directory('.', 'mobile_test.html')


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'ocr_available': ocr_extractor is not None,
        'ocr_engine': 'Google Vision API' if use_google_vision else 'Tesseract OCR'
    })


@app.route('/api/scan-bill', methods=['POST'])
def scan_bill():
    """
    Scan a bill image and return extracted data (without saving to sheets)

    Accepts: multipart/form-data with 'image' file
    Returns: JSON with extracted bill data
    """
    if ocr_extractor is None:
        return jsonify({
            'success': False,
            'error': 'OCR service not available'
        }), 500

    # Check if image is in request
    if 'image' not in request.files:
        return jsonify({
            'success': False,
            'error': 'No image file provided'
        }), 400

    file = request.files['image']

    # Check if file is selected
    if file.filename == '':
        return jsonify({
            'success': False,
            'error': 'No file selected'
        }), 400

    # Check if file is allowed
    if not allowed_file(file.filename):
        return jsonify({
            'success': False,
            'error': f'File type not allowed. Allowed types: {", ".join(config.ALLOWED_EXTENSIONS)}'
        }), 400

    try:
        # Read image bytes
        image_bytes = file.read()

        # Extract text using OCR
        ocr_text = ocr_extractor.extract_text_from_bytes(image_bytes)

        if not ocr_text:
            return jsonify({
                'success': False,
                'error': 'No text could be extracted from the image'
            }), 400

        # Parse bill data
        bill_data = bill_parser.parse_bill(ocr_text)

        # Validate data
        is_valid, errors = bill_parser.validate_data(bill_data)

        return jsonify({
            'success': True,
            'data': {
                'invoice_no': bill_data.get('invoice_no'),
                'bill_date': bill_data.get('bill_date'),
                'buyer': bill_data.get('buyer'),
                'total_amount': bill_data.get('total_amount')
            },
            'validation': {
                'is_valid': is_valid,
                'errors': errors
            },
            'ocr_engine': 'Google Vision API' if use_google_vision else 'Tesseract OCR'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/process-bill', methods=['POST'])
def process_bill():
    """
    Complete workflow: Scan bill, extract data, and save to Google Sheets

    Accepts: multipart/form-data with 'image' file
    Returns: JSON with processing result
    """
    if ocr_extractor is None:
        return jsonify({
            'success': False,
            'error': 'OCR service not available'
        }), 500

    # Check if image is in request
    if 'image' not in request.files:
        return jsonify({
            'success': False,
            'error': 'No image file provided'
        }), 400

    file = request.files['image']

    if file.filename == '':
        return jsonify({
            'success': False,
            'error': 'No file selected'
        }), 400

    if not allowed_file(file.filename):
        return jsonify({
            'success': False,
            'error': f'File type not allowed. Allowed types: {", ".join(config.ALLOWED_EXTENSIONS)}'
        }), 400

    try:
        # Read image bytes
        image_bytes = file.read()

        # Extract text using OCR
        ocr_text = ocr_extractor.extract_text_from_bytes(image_bytes)

        if not ocr_text:
            return jsonify({
                'success': False,
                'error': 'No text could be extracted from the image'
            }), 400

        # Parse bill data
        bill_data = bill_parser.parse_bill(ocr_text)

        # Validate data
        is_valid, errors = bill_parser.validate_data(bill_data)

        if not is_valid:
            return jsonify({
                'success': False,
                'error': 'Data validation failed',
                'validation_errors': errors,
                'extracted_data': {
                    'invoice_no': bill_data.get('invoice_no'),
                    'bill_date': bill_data.get('bill_date'),
                    'buyer': bill_data.get('buyer'),
                    'total_amount': bill_data.get('total_amount')
                }
            }), 400

        # Save to Google Sheets
        sheets = GoogleSheetsIntegration()
        result = sheets.append_bill_data(bill_data)

        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Bill processed and saved successfully',
                'data': {
                    'invoice_no': bill_data.get('invoice_no'),
                    'bill_date': bill_data.get('bill_date'),
                    'buyer': bill_data.get('buyer'),
                    'total_amount': bill_data.get('total_amount')
                },
                'sheets_result': result,
                'ocr_engine': 'Google Vision API' if use_google_vision else 'Tesseract OCR'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to save to Google Sheets',
                'details': result.get('error'),
                'extracted_data': {
                    'invoice_no': bill_data.get('invoice_no'),
                    'bill_date': bill_data.get('bill_date'),
                    'buyer': bill_data.get('buyer'),
                    'total_amount': bill_data.get('total_amount')
                }
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/test-connection', methods=['GET'])
def test_connection():
    """Test Google Sheets connection"""
    try:
        sheets = GoogleSheetsIntegration()
        result = sheets.validate_connection()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/bills', methods=['GET'])
def get_bills():
    """Retrieve all bills from Google Sheets"""
    try:
        sheets = GoogleSheetsIntegration()
        bills = sheets.get_all_bills()
        return jsonify({
            'success': True,
            'count': len(bills),
            'bills': bills
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    app.run(
        host=config.FLASK_HOST,
        port=config.FLASK_PORT,
        debug=config.FLASK_DEBUG
    )
