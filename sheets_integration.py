"""
Google Sheets Integration Module
"""
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import config


class GoogleSheetsIntegration:
    """Handle Google Sheets operations"""

    def __init__(self, credentials_path=None, spreadsheet_id=None):
        """
        Initialize Google Sheets client

        Args:
            credentials_path (str): Path to service account credentials JSON
            spreadsheet_id (str): Google Sheets spreadsheet ID
        """
        self.credentials_path = credentials_path or config.GOOGLE_SHEETS_CREDENTIALS
        self.spreadsheet_id = spreadsheet_id or config.SPREADSHEET_ID

        # Define the scope
        self.scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]

        # Authorize and create client
        try:
            creds = ServiceAccountCredentials.from_json_keyfile_name(
                self.credentials_path, self.scope
            )
            self.client = gspread.authorize(creds)
            self.spreadsheet = self.client.open_by_key(self.spreadsheet_id)
        except Exception as e:
            raise Exception(f'Google Sheets Authentication Error: {str(e)}')

    def get_or_create_sheet(self, sheet_name=None):
        """
        Get worksheet by name or create if doesn't exist

        Args:
            sheet_name (str): Name of the worksheet

        Returns:
            gspread.Worksheet: The worksheet object
        """
        sheet_name = sheet_name or config.SHEET_NAME

        try:
            worksheet = self.spreadsheet.worksheet(sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            # Create new worksheet with headers
            worksheet = self.spreadsheet.add_worksheet(
                title=sheet_name,
                rows=1000,
                cols=10
            )
            # Add headers
            headers = [
                'Scan Date',
                'Invoice No',
                'Bill Date',
                'Buyer',
                'Total Amount'
            ]
            worksheet.append_row(headers)

        return worksheet

    def append_bill_data(self, bill_data, sheet_name=None):
        """
        Append bill data as a new row in Google Sheets

        Args:
            bill_data (dict): Parsed bill data with keys:
                - invoice_no
                - bill_date
                - buyer
                - total_amount
            sheet_name (str): Name of the worksheet

        Returns:
            dict: Result with success status and row number
        """
        try:
            worksheet = self.get_or_create_sheet(sheet_name)

            # Prepare row data
            scan_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            row_data = [
                scan_date,
                bill_data.get('invoice_no', ''),
                bill_data.get('bill_date', ''),
                bill_data.get('buyer', ''),
                bill_data.get('total_amount', 0)
            ]

            # Append the row
            worksheet.append_row(row_data, value_input_option='USER_ENTERED')

            # Get the row number
            row_number = len(worksheet.get_all_values())

            return {
                'success': True,
                'row_number': row_number,
                'message': f'Data appended to row {row_number}'
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Failed to append data: {str(e)}'
            }

    def get_all_bills(self, sheet_name=None):
        """
        Retrieve all bills from the sheet

        Args:
            sheet_name (str): Name of the worksheet

        Returns:
            list: List of bill records
        """
        try:
            worksheet = self.get_or_create_sheet(sheet_name)
            records = worksheet.get_all_records()
            return records
        except Exception as e:
            raise Exception(f'Error retrieving bills: {str(e)}')

    def initialize_sheet(self, sheet_name=None):
        """
        Initialize a new sheet with headers

        Args:
            sheet_name (str): Name of the worksheet

        Returns:
            bool: Success status
        """
        try:
            self.get_or_create_sheet(sheet_name)
            return True
        except Exception as e:
            raise Exception(f'Error initializing sheet: {str(e)}')

    def validate_connection(self):
        """
        Validate Google Sheets connection

        Returns:
            dict: Validation result
        """
        try:
            spreadsheet = self.client.open_by_key(self.spreadsheet_id)
            return {
                'success': True,
                'spreadsheet_title': spreadsheet.title,
                'url': spreadsheet.url
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
