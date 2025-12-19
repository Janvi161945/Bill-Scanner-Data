"""
Local Testing Script - Test OCR and parsing without API calls
"""
import os
import sys
from bill_parser import BillParser
from ocr_extractor import OCRExtractor, TesseractOCRExtractor


def test_with_tesseract():
    """Test using Tesseract OCR (no API key needed)"""
    print("=" * 70)
    print("TESTING WITH TESSERACT OCR (LOCAL)")
    print("=" * 70)

    try:
        ocr = TesseractOCRExtractor()
        parser = BillParser()

        # Test with sample images
        photos_dir = 'photos'
        if not os.path.exists(photos_dir):
            print(f"Error: {photos_dir} directory not found")
            return

        image_files = [f for f in os.listdir(photos_dir) if f.endswith(('.jpg', '.jpeg', '.png'))]

        if not image_files:
            print(f"No images found in {photos_dir} directory")
            return

        for img_file in image_files[:3]:  # Test first 3 images
            img_path = os.path.join(photos_dir, img_file)
            print(f"\n{'=' * 70}")
            print(f"Processing: {img_file}")
            print('=' * 70)

            try:
                # Extract text
                print("\n1. Extracting text using OCR...")
                text = ocr.extract_text_from_image(img_path)

                if not text:
                    print("   ✗ No text extracted")
                    continue

                print(f"   ✓ Extracted {len(text)} characters")
                print("\n   First 500 characters of extracted text:")
                print("   " + "-" * 66)
                print("   " + text[:500].replace('\n', '\n   '))
                print("   " + "-" * 66)

                # Parse bill data
                print("\n2. Parsing bill data...")
                bill_data = parser.parse_bill(text)

                print(f"\n   Extracted Data:")
                print(f"   - Buyer: {bill_data.get('buyer', 'NOT FOUND')}")
                print(f"   - Total (Before Tax): {bill_data.get('total_before_tax', 'NOT FOUND')}")
                print(f"   - CGST: {bill_data.get('cgst', 'NOT FOUND')}")
                print(f"   - SGST: {bill_data.get('sgst', 'NOT FOUND')}")
                print(f"   - Grand Total: {bill_data.get('grand_total', 'NOT FOUND')}")

                # Validate
                print("\n3. Validating data...")
                is_valid, errors = parser.validate_data(bill_data)

                if is_valid:
                    print("   ✓ All fields extracted successfully!")
                else:
                    print(f"   ✗ Validation failed:")
                    for error in errors:
                        print(f"     - {error}")

            except Exception as e:
                print(f"   ✗ Error processing {img_file}: {str(e)}")

    except ImportError:
        print("✗ Tesseract OCR not installed")
        print("\nTo install Tesseract:")
        print("  Ubuntu/Debian: sudo apt-get install tesseract-ocr")
        print("  MacOS: brew install tesseract")
        print("  Then: pip install pytesseract")


def test_with_google_vision():
    """Test using Google Cloud Vision API"""
    print("\n" + "=" * 70)
    print("TESTING WITH GOOGLE CLOUD VISION API")
    print("=" * 70)

    try:
        ocr = OCRExtractor()
        parser = BillParser()

        # Test with sample images
        photos_dir = 'photos'
        if not os.path.exists(photos_dir):
            print(f"Error: {photos_dir} directory not found")
            return

        image_files = [f for f in os.listdir(photos_dir) if f.endswith(('.jpg', '.jpeg', '.png'))]

        if not image_files:
            print(f"No images found in {photos_dir} directory")
            return

        for img_file in image_files[:3]:  # Test first 3 images
            img_path = os.path.join(photos_dir, img_file)
            print(f"\n{'=' * 70}")
            print(f"Processing: {img_file}")
            print('=' * 70)

            try:
                # Extract text
                print("\n1. Extracting text using Google Vision API...")
                text = ocr.extract_text_from_image(img_path)

                if not text:
                    print("   ✗ No text extracted")
                    continue

                print(f"   ✓ Extracted {len(text)} characters")
                print("\n   First 500 characters of extracted text:")
                print("   " + "-" * 66)
                print("   " + text[:500].replace('\n', '\n   '))
                print("   " + "-" * 66)

                # Parse bill data
                print("\n2. Parsing bill data...")
                bill_data = parser.parse_bill(text)

                print(f"\n   Extracted Data:")
                print(f"   - Buyer: {bill_data.get('buyer', 'NOT FOUND')}")
                print(f"   - Total (Before Tax): {bill_data.get('total_before_tax', 'NOT FOUND')}")
                print(f"   - CGST: {bill_data.get('cgst', 'NOT FOUND')}")
                print(f"   - SGST: {bill_data.get('sgst', 'NOT FOUND')}")
                print(f"   - Grand Total: {bill_data.get('grand_total', 'NOT FOUND')}")

                # Validate
                print("\n3. Validating data...")
                is_valid, errors = parser.validate_data(bill_data)

                if is_valid:
                    print("   ✓ All fields extracted successfully!")
                else:
                    print(f"   ✗ Validation failed:")
                    for error in errors:
                        print(f"     - {error}")

            except Exception as e:
                print(f"   ✗ Error processing {img_file}: {str(e)}")

    except Exception as e:
        print(f"✗ Google Vision API not configured: {str(e)}")
        print("\nTo use Google Vision API:")
        print("  1. Create a Google Cloud project")
        print("  2. Enable Vision API")
        print("  3. Create service account and download JSON key")
        print("  4. Set environment variable: GOOGLE_APPLICATION_CREDENTIALS=path/to/key.json")


def main():
    """Main test function"""
    print("\n" + "=" * 70)
    print("BILL SCANNING SYSTEM - LOCAL TEST")
    print("=" * 70)

    # Check for command line argument
    if len(sys.argv) > 1:
        if sys.argv[1] == '--google':
            test_with_google_vision()
        elif sys.argv[1] == '--tesseract':
            test_with_tesseract()
        else:
            print("Usage: python test_local.py [--google|--tesseract]")
    else:
        # Try Google Vision first, fall back to Tesseract
        print("\nAttempting Google Vision API...")
        try:
            test_with_google_vision()
        except Exception:
            print("\nGoogle Vision API not available, trying Tesseract...")
            test_with_tesseract()

    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
