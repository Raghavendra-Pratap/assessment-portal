"""Grading engine for auto-grading assessments"""

from src.services.google_sheets import get_google_sheets_service

class GradingEngine:
    def __init__(self):
        self.google_sheets = get_google_sheets_service()
    
    def grade_response(self, question: dict, sheet_url: str) -> dict:
        """Grade a response based on question type"""
        question_type = question.get('type')
        
        if question_type == 'formula':
            return self.grade_formula_question(question, sheet_url)
        elif question_type == 'data-entry':
            return self.grade_data_entry_question(question, sheet_url)
        elif question_type == 'mcq':
            return self.grade_mcq_question(question, sheet_url)
        elif question_type == 'scenario':
            return {'auto_score': None, 'manual_required': True}
        else:
            return {'auto_score': 0, 'error': 'Unknown question type'}
    
    def grade_formula_question(self, question: dict, sheet_url: str) -> dict:
        """Grade a formula question"""
        answer_key = question.get('answer_key', {})
        points = question.get('points', 10)
        
        if not self.google_sheets:
            return {'auto_score': 0, 'error': 'Google Sheets API not configured'}
        
        sheet_id = self.google_sheets.extract_sheet_id(sheet_url)
        if not sheet_id:
            return {'auto_score': 0, 'error': 'Invalid sheet URL'}
        
        sheet_data = self.google_sheets.get_sheet_with_formulas(sheet_id)
        if not sheet_data:
            return {'auto_score': 0, 'error': 'Could not fetch sheet data'}
        
        # Get first sheet
        first_sheet = list(sheet_data.values())[0] if sheet_data else {}
        
        # Compare formulas and values
        formula_score = self._compare_formulas(first_sheet, answer_key)
        value_score = self._compare_values(first_sheet, answer_key)
        
        # 50% formula correctness, 50% output accuracy
        total_score = (formula_score + value_score) / 2
        
        return {
            'auto_score': round((total_score / 100) * points, 2),
            'formula_score': formula_score,
            'value_score': value_score
        }
    
    def grade_data_entry_question(self, question: dict, sheet_url: str) -> dict:
        """Grade a data entry question"""
        answer_key = question.get('answer_key', {})
        points = question.get('points', 10)
        
        if not self.google_sheets:
            return {'auto_score': 0, 'error': 'Google Sheets API not configured'}
        
        sheet_id = self.google_sheets.extract_sheet_id(sheet_url)
        if not sheet_id:
            return {'auto_score': 0, 'error': 'Invalid sheet URL'}
        
        sheet_data = self.google_sheets.get_sheet_with_formulas(sheet_id)
        if not sheet_data:
            return {'auto_score': 0, 'error': 'Could not fetch sheet data'}
        
        first_sheet = list(sheet_data.values())[0] if sheet_data else {}
        score = self._compare_data_entry(first_sheet, answer_key)
        
        return {
            'auto_score': round((score / 100) * points, 2),
            'details': self._get_data_entry_details(first_sheet, answer_key)
        }
    
    def grade_mcq_question(self, question: dict, sheet_url: str) -> dict:
        """Grade an MCQ question"""
        answer_key = question.get('answer_key', {})
        points = question.get('points', 10)
        
        correct_answer = answer_key.get('answer', '').strip().upper()
        
        if not self.google_sheets:
            return {'auto_score': 0, 'error': 'Google Sheets API not configured'}
        
        sheet_id = self.google_sheets.extract_sheet_id(sheet_url)
        if not sheet_id:
            return {'auto_score': 0, 'error': 'Invalid sheet URL'}
        
        values = self.google_sheets.get_sheet_values(sheet_id, 'A1:Z100')
        
        if values and len(values) > 0:
            user_answer = str(values[0][0]).strip().upper() if len(values[0]) > 0 else ''
            if user_answer == correct_answer:
                return {'auto_score': points}
        
        return {'auto_score': 0}
    
    def _compare_formulas(self, sheet_data: dict, answer_key: dict) -> float:
        """Compare formulas in sheet with answer key"""
        if 'formulas' not in answer_key:
            return 0
        
        matches = 0
        total = 0
        
        for cell_ref, expected_formula in answer_key['formulas'].items():
            total += 1
            actual_cell = sheet_data.get(cell_ref)
            
            if actual_cell and actual_cell.get('type') == 'formula':
                actual_formula = self._normalize_formula(actual_cell['value'])
                expected_formula_norm = self._normalize_formula(expected_formula)
                
                if actual_formula == expected_formula_norm:
                    matches += 1
        
        return (matches / total * 100) if total > 0 else 0
    
    def _compare_values(self, sheet_data: dict, answer_key: dict) -> float:
        """Compare calculated values in sheet with answer key"""
        if 'values' not in answer_key:
            return 0
        
        matches = 0
        total = 0
        tolerance = 0.01  # 1% tolerance for numeric values
        
        for cell_ref, expected_value in answer_key['values'].items():
            total += 1
            actual_cell = sheet_data.get(cell_ref)
            
            if actual_cell:
                actual_value = actual_cell.get('value')
                
                # Compare as numbers if both are numeric
                try:
                    actual_num = float(actual_value)
                    expected_num = float(expected_value)
                    
                    if abs(actual_num - expected_num) <= (abs(expected_num) * tolerance):
                        matches += 1
                except (ValueError, TypeError):
                    # Compare as strings
                    if str(actual_value).strip().upper() == str(expected_value).strip().upper():
                        matches += 1
        
        return (matches / total * 100) if total > 0 else 0
    
    def _compare_data_entry(self, sheet_data: dict, answer_key: dict) -> float:
        """Compare data entry values"""
        matches = 0
        total = 0
        tolerance = 0.01
        
        for cell_ref, expected_value in answer_key.items():
            total += 1
            actual_cell = sheet_data.get(cell_ref)
            
            if actual_cell:
                actual_value = actual_cell.get('value')
                
                try:
                    actual_num = float(actual_value)
                    expected_num = float(expected_value)
                    
                    if abs(actual_num - expected_num) <= (abs(expected_num) * tolerance):
                        matches += 1
                except (ValueError, TypeError):
                    if str(actual_value).strip().upper() == str(expected_value).strip().upper():
                        matches += 1
        
        return (matches / total * 100) if total > 0 else 0
    
    def _get_data_entry_details(self, sheet_data: dict, answer_key: dict) -> dict:
        """Get detailed comparison results for data entry"""
        details = {'correct': [], 'incorrect': []}
        
        for cell_ref, expected_value in answer_key.items():
            actual_cell = sheet_data.get(cell_ref)
            if actual_cell:
                actual_value = actual_cell.get('value')
                if str(actual_value).strip() == str(expected_value).strip():
                    details['correct'].append(cell_ref)
                else:
                    details['incorrect'].append({
                        'cell': cell_ref,
                        'expected': expected_value,
                        'actual': actual_value
                    })
        
        return details
    
    def _normalize_formula(self, formula: str) -> str:
        """Normalize formula for comparison"""
        if not formula:
            return ''
        # Remove spaces, convert to uppercase
        return ''.join(formula.upper().split())

