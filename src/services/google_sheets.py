"""Google Sheets API integration"""

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json
import re

class GoogleSheetsAPI:
    def __init__(self, credentials_json=None):
        """Initialize Google Sheets API client"""
        self.credentials_json = credentials_json
        self.service = None
        self.drive_service = None
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialize Google API services"""
        if self.credentials_json:
            try:
                creds_dict = json.loads(self.credentials_json) if isinstance(self.credentials_json, str) else self.credentials_json
                credentials = service_account.Credentials.from_service_account_info(
                    creds_dict,
                    scopes=[
                        'https://www.googleapis.com/auth/spreadsheets',
                        'https://www.googleapis.com/auth/drive'
                    ]
                )
                
                self.service = build('sheets', 'v4', credentials=credentials)
                self.drive_service = build('drive', 'v3', credentials=credentials)
            except Exception as e:
                try:
                    import streamlit as st
                    st.error(f"Error initializing Google Sheets API: {str(e)}")
                except:
                    print(f"Error initializing Google Sheets API: {str(e)}")
    
    def extract_sheet_id(self, url: str) -> str:
        """Extract sheet ID from Google Sheets URL"""
        pattern = r'/spreadsheets/d/([a-zA-Z0-9-_]+)'
        match = re.search(pattern, url)
        return match.group(1) if match else None
    
    def copy_sheet(self, source_sheet_id: str, title: str, share_with_email: str = None) -> dict:
        """Copy a Google Sheet and optionally share with a user"""
        if not self.drive_service:
            return {'success': False, 'error': 'Drive service not initialized'}
        
        try:
            # Copy the file
            copied_file = self.drive_service.files().copy(
                fileId=source_sheet_id,
                body={'name': title}
            ).execute()
            
            new_sheet_id = copied_file['id']
            
            # Share with email if provided
            if share_with_email:
                permission = {
                    'type': 'user',
                    'role': 'writer',
                    'emailAddress': share_with_email
                }
                self.drive_service.permissions().create(
                    fileId=new_sheet_id,
                    body=permission
                ).execute()
            
            return {
                'success': True,
                'sheet_id': new_sheet_id,
                'url': f"https://docs.google.com/spreadsheets/d/{new_sheet_id}"
            }
        except HttpError as e:
            return {'success': False, 'error': str(e)}
    
    def get_sheet_values(self, sheet_id: str, range_name: str = 'A1:Z1000'):
        """Get values from a sheet"""
        if not self.service:
            return None
        
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range=range_name
            ).execute()
            return result.get('values', [])
        except HttpError as e:
            return None
    
    def get_sheet_with_formulas(self, sheet_id: str):
        """Get sheet data including formulas"""
        if not self.service:
            return None
        
        try:
            result = self.service.spreadsheets().get(
                spreadsheetId=sheet_id,
                includeGridData=True
            ).execute()
            
            sheet_data = {}
            for sheet in result.get('sheets', []):
                sheet_title = sheet['properties']['title']
                sheet_data[sheet_title] = {}
                
                for row_data in sheet.get('data', [{}])[0].get('rowData', []):
                    for cell_data in row_data.get('values', []):
                        cell_ref = self._get_cell_reference(
                            row_data.get('startRow', 0),
                            cell_data.get('startColumn', 0)
                        )
                        
                        if 'userEnteredValue' in cell_data:
                            entered_value = cell_data['userEnteredValue']
                            if 'formulaValue' in entered_value:
                                sheet_data[sheet_title][cell_ref] = {
                                    'type': 'formula',
                                    'value': entered_value['formulaValue']
                                }
                            elif 'numberValue' in entered_value:
                                sheet_data[sheet_title][cell_ref] = {
                                    'type': 'number',
                                    'value': entered_value['numberValue']
                                }
                            elif 'stringValue' in entered_value:
                                sheet_data[sheet_title][cell_ref] = {
                                    'type': 'string',
                                    'value': entered_value['stringValue']
                                }
            
            return sheet_data
        except HttpError as e:
            return None
    
    def _get_cell_reference(self, row: int, col: int) -> str:
        """Convert row/col indices to cell reference (e.g., A1, B2)"""
        col_letter = chr(65 + col % 26)
        if col >= 26:
            col_letter = chr(64 + col // 26) + col_letter
        return f"{col_letter}{row + 1}"
    
    def create_sheet(self, title: str, share_with_email: str = None) -> dict:
        """Create a new Google Sheet"""
        if not self.service:
            return {'success': False, 'error': 'Sheets service not initialized'}
        
        try:
            spreadsheet = {
                'properties': {
                    'title': title
                },
                'sheets': [{
                    'properties': {
                        'title': 'Sheet1'
                    }
                }]
            }
            
            result = self.service.spreadsheets().create(body=spreadsheet).execute()
            sheet_id = result['spreadsheetId']
            
            # Share with email if provided
            if share_with_email and self.drive_service:
                try:
                    permission = {
                        'type': 'user',
                        'role': 'writer',
                        'emailAddress': share_with_email
                    }
                    self.drive_service.permissions().create(
                        fileId=sheet_id,
                        body=permission
                    ).execute()
                except Exception as e:
                    # Log but don't fail if sharing fails
                    pass
            
            return {
                'success': True,
                'sheet_id': sheet_id,
                'url': f"https://docs.google.com/spreadsheets/d/{sheet_id}",
                'title': title
            }
        except HttpError as e:
            return {'success': False, 'error': str(e)}
    
    def list_sheets(self, max_results: int = 50) -> list:
        """List Google Sheets accessible by the service account"""
        if not self.drive_service:
            return []
        
        try:
            results = self.drive_service.files().list(
                q="mimeType='application/vnd.google-apps.spreadsheet' and trashed=false",
                pageSize=max_results,
                fields="files(id, name, createdTime, modifiedTime, webViewLink)"
            ).execute()
            
            sheets = results.get('files', [])
            return [
                {
                    'id': sheet['id'],
                    'name': sheet['name'],
                    'url': sheet.get('webViewLink', f"https://docs.google.com/spreadsheets/d/{sheet['id']}"),
                    'created': sheet.get('createdTime', ''),
                    'modified': sheet.get('modifiedTime', '')
                }
                for sheet in sheets
            ]
        except HttpError as e:
            return []
    
    def update_sheet_values(self, sheet_id: str, range_name: str, values: list) -> dict:
        """Update values in a sheet"""
        if not self.service:
            return {'success': False, 'error': 'Sheets service not initialized'}
        
        try:
            body = {
                'values': values
            }
            result = self.service.spreadsheets().values().update(
                spreadsheetId=sheet_id,
                range=range_name,
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            
            return {
                'success': True,
                'updated_cells': result.get('updatedCells', 0)
            }
        except HttpError as e:
            return {'success': False, 'error': str(e)}
    
    def get_sheet_info(self, sheet_id: str) -> dict:
        """Get basic information about a sheet"""
        if not self.service:
            return None
        
        try:
            result = self.service.spreadsheets().get(spreadsheetId=sheet_id).execute()
            return {
                'title': result['properties']['title'],
                'sheet_id': sheet_id,
                'url': f"https://docs.google.com/spreadsheets/d/{sheet_id}",
                'sheets': [
                    {
                        'title': sheet['properties']['title'],
                        'sheet_id': sheet['properties']['sheetId']
                    }
                    for sheet in result.get('sheets', [])
                ]
            }
        except HttpError as e:
            return None
    
    def is_configured(self) -> bool:
        """Check if Google Sheets API is properly configured"""
        return self.service is not None and self.drive_service is not None

def load_google_credentials():
    """Load Google credentials from config file"""
    import os
    credentials_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config', 'google_credentials.json')
    
    if os.path.exists(credentials_path):
        try:
            with open(credentials_path, 'r') as f:
                return json.load(f)
        except Exception:
            return None
    return None

def get_google_sheets_service():
    """Get Google Sheets service from session state or config file"""
    try:
        import streamlit as st
        if 'google_sheets_service' not in st.session_state:
            # First, try to load from config file (admin settings)
            credentials = load_google_credentials()
            
            if credentials:
                st.session_state.google_sheets_service = GoogleSheetsAPI(credentials)
            else:
                # Fallback: try session state settings
                settings = st.session_state.get('settings', {})
                credentials = settings.get('google_service_account', '')
                if credentials:
                    st.session_state.google_sheets_service = GoogleSheetsAPI(credentials)
                else:
                    # Fallback: try database
                    from src.database import SessionLocal, Recruiter
                    if st.session_state.get('user'):
                        db = SessionLocal()
                        try:
                            user_id = st.session_state.user['id']
                            recruiter = db.query(Recruiter).filter(Recruiter.id == user_id).first()
                            if recruiter and recruiter.storage_config:
                                creds = recruiter.storage_config.get('google_service_account', '')
                                if creds:
                                    st.session_state.google_sheets_service = GoogleSheetsAPI(creds)
                                else:
                                    st.session_state.google_sheets_service = None
                            else:
                                st.session_state.google_sheets_service = None
                        finally:
                            db.close()
                    else:
                        st.session_state.google_sheets_service = None
        
        # Refresh service if credentials file changed
        if st.session_state.google_sheets_service:
            credentials = load_google_credentials()
            if credentials and st.session_state.google_sheets_service.credentials_json != credentials:
                st.session_state.google_sheets_service = None
                if credentials:
                    st.session_state.google_sheets_service = GoogleSheetsAPI(credentials)
        
        return st.session_state.google_sheets_service
    except Exception as e:
        return None

