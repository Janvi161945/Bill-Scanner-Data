"""
Bill Data Parser - Extracts structured data from OCR text
"""
import re
from typing import Dict, Optional, Tuple, List


class BillParser:
    """Parse Tally bill text and extract required fields"""

    def __init__(self):
        """Initialize parser with regex patterns"""
        # Patterns for extracting data
        self.buyer_patterns = [
            r'Buyer\s*\(Bill\s+to\)\s*\n([^\n]+)',
            r'Buyer\s*:\s*([^\n]+)',
            r'Bill\s+to\s*:\s*([^\n]+)',
        ]

        self.invoice_patterns = [
            r'Invoice\s+No\.?\s*[:\s]*(\d+)',
            r'Invoice\s+Number\s*[:\s]*(\d+)',
            r'Bill\s+No\.?\s*[:\s]*(\d+)',
        ]

        self.date_patterns = [
            r'Dated\s*\n\s*(\d{1,2}[-/]\w{3}[-/]\d{2,4})',  # 14-Oct-25
            r'Dated[:\s]+(\d{1,2}[-/]\w{3}[-/]\d{2,4})',
            r'Date[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',  # 14/10/2025
            r'Invoice\s+No\.?\s+Dated\s*\n\s*\d+\s*\n\s*(\d{1,2}[-/]\w{3}[-/]\d{2,4})',  # Invoice No. Dated format
        ]

        self.total_before_tax_patterns = [
            r'Taxable\s*Value\s*[:\s]*(\d+(?:,\d+)*(?:\.\d+)?)',
            r'Total\s*(?:before|without)\s*tax\s*[:\s]*(?:₹|Rs\.?)?\s*(\d+(?:,\d+)*(?:\.\d+)?)',
            r'Sub\s*Total\s*[:\s]*(?:₹|Rs\.?)?\s*(\d+(?:,\d+)*(?:\.\d+)?)',
        ]

        self.cgst_patterns = [
            r'CGST\s*[:\s]*(?:Rate\s*)?(?:\d+(?:\.\d+)?%?)?\s*(?:Amount\s*)?[:\s]*(?:₹|Rs\.?)?\s*(\d+(?:,\d+)*(?:\.\d+)?)',
            r'Central\s*GST\s*[:\s]*(?:₹|Rs\.?)?\s*(\d+(?:,\d+)*(?:\.\d+)?)',
        ]

        self.sgst_patterns = [
            r'SGST(?:/UTGST)?\s*[:\s]*(?:Rate\s*)?(?:\d+(?:\.\d+)?%?)?\s*(?:Amount\s*)?[:\s]*(?:₹|Rs\.?)?\s*(\d+(?:,\d+)*(?:\.\d+)?)',
            r'State\s*GST\s*[:\s]*(?:₹|Rs\.?)?\s*(\d+(?:,\d+)*(?:\.\d+)?)',
            r'UTGST\s*[:\s]*(?:Rate\s*)?(?:\d+(?:\.\d+)?%?)?\s*(?:Amount\s*)?[:\s]*(?:₹|Rs\.?)?\s*(\d+(?:,\d+)*(?:\.\d+)?)',
        ]

        self.grand_total_patterns = [
            r'Total\s*Tax\s*Amount\s*[:\s]*(?:₹|Rs\.?)?\s*(\d+(?:,\d+)*(?:\.\d+)?)',
            r'Grand\s*Total\s*[:\s]*(?:₹|Rs\.?)?\s*(\d+(?:,\d+)*(?:\.\d+)?)',
            r'Total\s*[:\s]*(?:₹|Rs\.?)?\s*(\d+(?:,\d+)*(?:\.\d+)?)(?:\s*₹|\s*Rs\.?|\s*INR)?(?:\s*$|\s*\n)',
            r'Amount\s*Chargeable.*?\n.*?(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:₹|Rs\.?|INR)',
        ]

    def clean_number(self, value: str) -> Optional[float]:
        """
        Clean and convert string to float

        Args:
            value (str): Number string with potential formatting

        Returns:
            float: Cleaned numeric value or None
        """
        if not value:
            return None

        try:
            # Remove currency symbols, commas, and extra spaces (but NOT decimal points)
            cleaned = re.sub(r'[₹Rs,\s]', '', value)
            # Remove any non-numeric characters except decimal point
            cleaned = re.sub(r'[^\d.]', '', cleaned)

            if cleaned:
                return float(cleaned)
            return None
        except (ValueError, AttributeError):
            return None

    def extract_buyer(self, text: str) -> str:
        """Extract buyer/party name from text"""
        for pattern in self.buyer_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                buyer = match.group(1).strip()
                # Clean up the buyer name (remove extra info)
                buyer = re.split(r'\n|Contact|Mobile|Phone', buyer, maxsplit=1)[0].strip()
                return buyer
        return ""

    def extract_invoice_no(self, text: str) -> str:
        """Extract invoice number from text"""
        # Pattern 1: "Invoice No." with "Dated" on same line, number on next line
        pattern1 = r'Invoice\s+No\.?.*?\n\s*(\d+)'
        match = re.search(pattern1, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()

        # Pattern 2: "Invoice No: 123" on same line
        for pattern in self.invoice_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return ""

    def extract_bill_date(self, text: str) -> str:
        """Extract bill date from text"""
        for pattern in self.date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return ""

    def extract_total_before_tax(self, text: str) -> Optional[float]:
        """Extract total amount before tax"""
        # Pattern 1: "Total:" on one line, amount on next line
        pattern1 = r'Total:\s*\n[^\n]*?\n\s*(\d+(?:,\d+)*\.\d+)'
        match = re.search(pattern1, text, re.IGNORECASE)
        if match:
            value = self.clean_number(match.group(1))
            if value and value > 0:
                return value

        # Pattern 2: "Taxable Value" with amount in tax table
        pattern2 = r'Taxable\s+Value.*?(\d+(?:,\d+)*\.\d+)\s+\d+(?:\.\d+)?%'
        match = re.search(pattern2, text, re.IGNORECASE | re.DOTALL)
        if match:
            value = self.clean_number(match.group(1))
            if value and value > 0:
                return value

        # Pattern 3: Simple "Total:" followed by amount on same line
        pattern3 = r'Total:\s*(\d+(?:,\d+)*\.\d+)'
        match = re.search(pattern3, text, re.IGNORECASE)
        if match:
            value = self.clean_number(match.group(1))
            if value and value > 0:
                return value

        # Fallback to other patterns
        for pattern in self.total_before_tax_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                value = self.clean_number(match.group(1))
                if value and value > 0:
                    return value
        return None

    def extract_cgst(self, text: str) -> Optional[float]:
        """Extract CGST amount"""
        # Simple approach: Find all decimal numbers and look for patterns
        # In Tally bills, CGST appears in the bottom tax summary
        # Look for pattern where we have taxable value followed by two equal smaller amounts

        # First try: explicit CGST label
        cgst_pattern = r'(?:^|\n)\s*CGST[^\d]*(\d+\.\d+)'
        match = re.search(cgst_pattern, text, re.MULTILINE)
        if match:
            value = self.clean_number(match.group(1))
            if value and 0 < value < 100000:
                return value

        # Second try: Look in tax summary - find smaller amounts after "Total:"
        # Extract all decimal numbers after "Total:" keyword
        total_idx = text.rfind('Total:')
        if total_idx != -1:
            after_total = text[total_idx:]
            # Find all small decimal amounts (likely tax amounts)
            amounts = re.findall(r'\b(\d+\.\d{2})\b', after_total)
            # Filter for reasonable tax amounts (> 0, < 100000)
            tax_amounts = [float(a) for a in amounts if 0 < float(a) < 100000]
            # CGST and SGST are usually equal and appear as a pair
            if len(tax_amounts) >= 2:
                # Look for two consecutive equal values
                for i in range(len(tax_amounts) - 1):
                    if tax_amounts[i] == tax_amounts[i+1]:
                        return tax_amounts[i]
                # If no equal pair, return second smallest (likely CGST)
                if len(tax_amounts) >= 2:
                    sorted_amounts = sorted(tax_amounts)
                    return sorted_amounts[0]  # Smallest is likely CGST

        # Fallback to other patterns
        for pattern in self.cgst_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                value = self.clean_number(match.group(1))
                if value and value > 0:
                    return value
        return None

    def extract_sgst(self, text: str) -> Optional[float]:
        """Extract SGST/UTGST amount"""
        # First try: explicit SGST label
        sgst_pattern = r'(?:^|\n)\s*SGST[^\d]*(\d+\.\d+)'
        match = re.search(sgst_pattern, text, re.MULTILINE)
        if match:
            value = self.clean_number(match.group(1))
            if value and 0 < value < 100000:
                return value

        # Second try: Same logic as CGST - find matching pair or smallest value
        total_idx = text.rfind('Total:')
        if total_idx != -1:
            after_total = text[total_idx:]
            amounts = re.findall(r'\b(\d+\.\d{2})\b', after_total)
            tax_amounts = [float(a) for a in amounts if 0 < float(a) < 100000]
            if len(tax_amounts) >= 2:
                # Look for two consecutive equal values
                for i in range(len(tax_amounts) - 1):
                    if tax_amounts[i] == tax_amounts[i+1]:
                        return tax_amounts[i+1]  # Return second one for SGST
                # If no equal pair, return second smallest (likely SGST)
                if len(tax_amounts) >= 2:
                    sorted_amounts = sorted(tax_amounts)
                    # If there are exactly 2 small values of same amount, return the second
                    if len(sorted_amounts) >= 2 and sorted_amounts[0] == sorted_amounts[1]:
                        return sorted_amounts[1]
                    # Otherwise return second smallest
                    return sorted_amounts[1] if len(sorted_amounts) > 1 else sorted_amounts[0]

        # Fallback to other patterns
        for pattern in self.sgst_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                value = self.clean_number(match.group(1))
                if value and value > 0:
                    return value
        return None

    def extract_grand_total(self, text: str) -> Optional[float]:
        """Extract grand total (with tax)"""
        # Look for the highest total value, typically the grand total
        max_total = None

        for pattern in self.grand_total_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                value = self.clean_number(match.group(1))
                if value and value > 0:
                    if max_total is None or value > max_total:
                        max_total = value

        return max_total

    def extract_total_amount(self, text: str) -> Optional[float]:
        """
        Extract total amount using 'Amount Chargeable (in words)' as reference
        This is the most reliable way to get the correct total
        """
        # Pattern 1: Look for amount with ₹ symbol AFTER "Amount Chargeable (in words)"
        # This is the most reliable - the amount appears a few lines after the words
        chargeable_idx = text.find('Amount Chargeable (in words)')
        if chargeable_idx > 0:
            # Look in the next 300 characters after "Amount Chargeable (in words)"
            after_section = text[chargeable_idx:chargeable_idx + 300]
            # Find amounts with ₹ symbol (like "280.00 ₹" or "3,102.00 ₹")
            # IMPORTANT: Include comma in the pattern to handle amounts like 3,102.00
            amounts_with_rupee = re.findall(r'([\d,]+(?:\.\d+)?)\s*₹', after_section)
            if amounts_with_rupee:
                # The first amount with ₹ is usually the total
                value = self.clean_number(amounts_with_rupee[0])
                if value and value > 10:  # Sanity check - total should be > 10
                    return value

        # Pattern 2: Look for pattern "words\n...\nAmount ₹"
        word_pattern = r'Amount\s+Chargeable\s*\(in\s+words\).*?([\d,]+(?:\.\d+)?)\s*₹'
        match = re.search(word_pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            value = self.clean_number(match.group(1))
            if value and value > 0:
                return value

        # Pattern 3: Search backwards from "Amount Chargeable" to find largest amount
        chargeable_idx = text.lower().find('amount chargeable')
        if chargeable_idx > 0:
            # Look in the 500 characters before "Amount Chargeable"
            before_section = text[max(0, chargeable_idx - 500):chargeable_idx]
            amounts = re.findall(r'(\d+(?:\.\d+)?)', before_section)
            if amounts:
                # Get the largest amount (likely the total)
                amounts_float = [float(a) for a in amounts if float(a) > 10]
                if amounts_float:
                    return max(amounts_float)

        # Fallback: Use grand_total method
        return self.extract_grand_total(text)

    def parse_bill(self, ocr_text: str) -> Dict[str, any]:
        """
        Parse bill text and extract all required fields

        Args:
            ocr_text (str): Text extracted from OCR

        Returns:
            dict: Extracted bill data with validation
        """
        # Extract required fields
        invoice_no = self.extract_invoice_no(ocr_text)
        bill_date = self.extract_bill_date(ocr_text)
        buyer = self.extract_buyer(ocr_text)
        total_amount = self.extract_total_amount(ocr_text)

        result = {
            'invoice_no': invoice_no,
            'bill_date': bill_date,
            'buyer': buyer,
            'total_amount': total_amount,
            'success': all([
                invoice_no,
                bill_date,
                buyer,
                total_amount is not None
            ]),
            'raw_text': ocr_text
        }

        return result

    def validate_data(self, data: Dict) -> Tuple[bool, List]:
        """
        Validate extracted data

        Args:
            data (dict): Parsed bill data

        Returns:
            tuple: (is_valid, list_of_errors)
        """
        errors = []

        if not data.get('invoice_no'):
            errors.append("Invoice number not found")

        if not data.get('bill_date'):
            errors.append("Bill date not found")

        if not data.get('buyer'):
            errors.append("Buyer name not found")

        if data.get('total_amount') is None or data.get('total_amount') <= 0:
            errors.append("Total amount not found or invalid")

        return len(errors) == 0, errors
