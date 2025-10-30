"""Admin Assessments Page"""

import streamlit as st
import json
import uuid
from datetime import datetime, timedelta
from src.database import SessionLocal, Assessment, Question, Invitation, Recruiter
from src.utils.auth import check_auth

def render():
    st.title("📝 Assessments")
    
    if not check_auth():
        st.error("Please login first")
        return
    
    db = SessionLocal()
    try:
        user_id = st.session_state.user['id']
        
        # Check if we should create new or edit existing
        if st.session_state.get('create_new', False):
            st.session_state.create_new = False
            create_assessment_advanced(db, user_id)
        elif 'edit_assessment_id' in st.session_state:
            edit_assessment_id = st.session_state.edit_assessment_id
            del st.session_state.edit_assessment_id
            edit_assessment(db, user_id, edit_assessment_id)
        else:
            list_assessments(db, user_id)
            
    finally:
        db.close()

def list_assessments(db, user_id):
    """List all assessments"""
    col1, col2 = st.columns([3, 1])
    
    with col2:
        if st.button("➕ Create New Assessment", use_container_width=True, type="primary"):
            st.session_state.create_new = True
            st.rerun()
    
    assessments = db.query(Assessment).filter(Assessment.recruiter_id == user_id).order_by(Assessment.created_at.desc()).all()
    
    if not assessments:
        st.info("No assessments yet. Create your first assessment!")
        if st.button("Create Assessment"):
            st.session_state.create_new = True
            st.rerun()
        return
    
    for assessment in assessments:
        with st.container():
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.subheader(assessment.title)
                if assessment.description:
                    st.caption(assessment.description[:200])
                st.write(f"⏱️ Duration: {assessment.duration_minutes} minutes")
                st.write(f"📅 Created: {assessment.created_at.strftime('%Y-%m-%d')}")
            
            with col2:
                questions_count = db.query(Question).filter(Question.assessment_id == assessment.id).count()
                st.metric("Questions", questions_count)
            
            with col3:
                sessions_count = db.query(Session).filter(Session.assessment_id == assessment.id).count()
                st.metric("Sessions", sessions_count)
            
            col_a, col_b, col_c, col_d = st.columns(4)
            with col_a:
                if st.button("✏️ Edit", key=f"edit_{assessment.id}"):
                    st.session_state.edit_assessment_id = assessment.id
                    st.rerun()
            with col_b:
                if st.button("👥 Invite", key=f"invite_{assessment.id}"):
                    st.session_state.invite_assessment_id = assessment.id
                    invite_candidate(db, assessment.id, user_id)
            with col_c:
                if st.button("📊 Sessions", key=f"sessions_{assessment.id}"):
                    st.session_state.filter_assessment_id = assessment.id
                    st.session_state.page = 'sessions'
                    st.rerun()
            with col_d:
                if st.button("🗑️ Delete", key=f"delete_{assessment.id}"):
                    db.delete(assessment)
                    db.commit()
                    st.success("Assessment deleted!")
                    st.rerun()
            
            st.divider()

def create_assessment(db, user_id):
    """Create a new assessment"""
    st.subheader("Create New Assessment")
    
    with st.form("create_assessment_form"):
        title = st.text_input("Assessment Title *", placeholder="Excel Skills Assessment")
        description = st.text_area("Description", placeholder="Describe the assessment...")
        duration_minutes = st.number_input("Duration (minutes) *", min_value=1, value=60)
        
        submitted = st.form_submit_button("Create Assessment", use_container_width=True)
        
        if submitted:
            if not title:
                st.error("Title is required!")
                return
            
            assessment = Assessment(
                recruiter_id=user_id,
                title=title,
                description=description,
                duration_minutes=duration_minutes,
                settings={}
            )
            
            db.add(assessment)
            db.commit()
            
            st.success(f"Assessment '{title}' created successfully!")
            st.session_state.edit_assessment_id = assessment.id
            st.session_state.page = 'assessments'
            st.rerun()

def create_assessment_advanced(db, user_id):
    """Create a new assessment with question builder UI similar to plugin"""
    # Draft state in session
    draft = st.session_state.get('assessment_draft', {
        'title': '',
        'questions': []
    })
    st.session_state.assessment_draft = draft

    # Top bar: title input and actions
    top_left, top_right = st.columns([4, 2])
    with top_left:
        draft['title'] = st.text_input("Enter assessment name...", value=draft.get('title', ''), placeholder="New Assessment")
    with top_right:
        c1, c2, c3 = st.columns([1, 1, 1])
        with c1:
            st.button("Import", key="import_btn", disabled=True)
        with c2:
            if st.button("Cancel"):
                st.session_state.assessment_draft = {'title': '', 'questions': []}
                st.session_state.page = 'assessments'
                st.rerun()
        with c3:
            if st.button("Save Assessment", type="primary"):
                if not draft['title']:
                    st.error("Assessment name is required")
                else:
                    # Persist assessment and questions
                    assessment = Assessment(
                        recruiter_id=user_id,
                        title=draft['title'],
                        description='',
                        duration_minutes=60,
                        settings={}
                    )
                    db.add(assessment)
                    db.commit()

                    for idx, q in enumerate(draft['questions'], start=1):
                        question = Question(
                            assessment_id=assessment.id,
                            type=q['type'],
                            question_text=q['text'],
                            section_name=q.get('section') or None,
                            sheet_template_url=q.get('sheet_url') or None,
                            answer_key=q.get('answer_key') or {},
                            points=q['score'],
                            display_order=idx
                        )
                        db.add(question)
                    db.commit()

                    st.session_state.assessment_draft = {'title': '', 'questions': []}
                    st.success("Assessment created")
                    st.session_state.page = 'assessments'
                    st.rerun()

    st.divider()

    # Two-column layout: left panel - question editor; right - sheet placeholder
    left, right = st.columns([1, 2])

    with left:
        st.markdown("#### Question Settings")
        with st.form("question_builder_form"):
            st.markdown("**Question 01**")
            section_name = st.text_input("Section Name", placeholder="e.g., Excel Basics, Advanced Formulas")
            question_type = st.selectbox("Question Type *", ["formula", "data-entry", "mcq", "scenario"], index=0)
            question_text = st.text_area("Question Text *", placeholder="Enter your question...")
            score = st.number_input("Score *", min_value=1, value=10)
            mandatory = st.toggle("Mandatory Question", value=True)
            time_bound = st.toggle("Time Bound", value=False)
            negative_marking = st.toggle("Enable Negative Marking", value=False)
            instructions = st.text_area("Instructions (if any)", placeholder="Additional instructions for the candidate...")
            sheet_url = st.text_input("Google Sheet ID or URL", placeholder="Enter Google Sheet ID or paste full URL...")

            add_q = st.form_submit_button("Save Question", use_container_width=True)

            if add_q:
                if not question_text:
                    st.error("Question text is required")
                else:
                    draft['questions'].append({
                        'type': question_type,
                        'text': question_text,
                        'section': section_name,
                        'score': int(score),
                        'mandatory': mandatory,
                        'time_bound': time_bound,
                        'negative_marking': negative_marking,
                        'instructions': instructions,
                        'sheet_url': sheet_url,
                        'answer_key': {}
                    })
                    st.success("Question saved to draft")

        if st.button("+ Add Question", use_container_width=True):
            pass  # The form already adds on submit; button present for UX parity

    with right:
        st.markdown("#### Sheet 1")
        if not draft['questions']:
            st.info("No Questions Yet\n\nAdd a question on the left to get started with Google Sheets integration")
        else:
            for idx, q in enumerate(draft['questions'], start=1):
                with st.expander(f"Question {idx}: {q['type']} - {q['text'][:40]}"):
                    st.write(q)

def edit_assessment(db, user_id, assessment_id):
    """Edit an existing assessment"""
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    
    if not assessment or assessment.recruiter_id != user_id:
        st.error("Assessment not found")
        st.session_state.page = 'assessments'
        st.rerun()
        return
    
    st.subheader(f"Edit Assessment: {assessment.title}")
    
    # Basic info
    with st.form("edit_assessment_form"):
        title = st.text_input("Assessment Title *", value=assessment.title)
        description = st.text_area("Description", value=assessment.description or "")
        duration_minutes = st.number_input("Duration (minutes) *", min_value=1, value=assessment.duration_minutes)
        
        submitted = st.form_submit_button("Save Changes", use_container_width=True)
        
        if submitted:
            assessment.title = title
            assessment.description = description
            assessment.duration_minutes = duration_minutes
            assessment.updated_at = datetime.utcnow()
            
            db.commit()
            st.success("Assessment updated!")
            st.rerun()
    
    st.divider()
    
    # Questions section
    st.subheader("Questions")
    
    questions = db.query(Question).filter(Question.assessment_id == assessment_id).order_by(Question.display_order).all()
    
    if st.button("➕ Add Question", type="primary"):
        add_question_form(db, assessment_id)
    elif st.button("📥 Import from Google Sheet"):
        import_questions_form(db, assessment_id)
    
    if questions:
        for idx, question in enumerate(questions, 1):
            with st.expander(f"Question {idx}: {question.question_text[:50]}... ({question.type})"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Type:** {question.type}")
                    st.write(f"**Points:** {question.points}")
                    if question.section_name:
                        st.write(f"**Section:** {question.section_name}")
                
                with col2:
                    if st.button("Edit", key=f"edit_q_{question.id}"):
                        edit_question_form(db, question)
                    if st.button("Delete", key=f"delete_q_{question.id}"):
                        db.delete(question)
                        db.commit()
                        st.rerun()
    
    if st.button("← Back to Assessments"):
        st.session_state.page = 'assessments'
        st.rerun()

def add_question_form(db, assessment_id):
    """Form to add a new question"""
    with st.form("add_question_form"):
        question_type = st.selectbox("Question Type *", ["formula", "data-entry", "mcq", "scenario"])
        section_name = st.text_input("Section Name", placeholder="e.g., Excel Basics")
        question_text = st.text_area("Question Text *", placeholder="Enter the question...")
        sheet_template_url = st.text_input("Sheet Template URL", placeholder="https://docs.google.com/spreadsheets/d/...")
        points = st.number_input("Points", min_value=1, value=10)
        
        # Answer key
        st.subheader("Answer Key")
        answer_key_text = st.text_area("Answer Key (JSON format)", 
                                       placeholder='{"B2": "=VLOOKUP(A2,D2:E10,2,FALSE)"} for formula\n{"answer": "A"} for MCQ')
        
        submitted = st.form_submit_button("Add Question", use_container_width=True)
        
        if submitted:
            if not question_text:
                st.error("Question text is required!")
                return
            
            try:
                answer_key = json.loads(answer_key_text) if answer_key_text else {}
            except json.JSONDecodeError:
                st.error("Invalid JSON format for answer key!")
                return
            
            # Get next display order
            max_order = db.query(Question).filter(Question.assessment_id == assessment_id).count()
            
            question = Question(
                assessment_id=assessment_id,
                type=question_type,
                question_text=question_text,
                section_name=section_name if section_name else None,
                sheet_template_url=sheet_template_url if sheet_template_url else None,
                answer_key=answer_key,
                points=points,
                display_order=max_order + 1
            )
            
            db.add(question)
            db.commit()
            
            st.success("Question added!")
            st.rerun()

def edit_question_form(db, question):
    """Form to edit a question"""
    st.subheader(f"Edit Question")
    
    with st.form("edit_question_form"):
        question_type = st.selectbox("Question Type *", ["formula", "data-entry", "mcq", "scenario"],
                                    index=["formula", "data-entry", "mcq", "scenario"].index(question.type))
        section_name = st.text_input("Section Name", value=question.section_name or "")
        question_text = st.text_area("Question Text *", value=question.question_text)
        sheet_template_url = st.text_input("Sheet Template URL", value=question.sheet_template_url or "")
        points = st.number_input("Points", min_value=1, value=question.points)
        
        answer_key_text = st.text_area("Answer Key (JSON format)", 
                                      value=json.dumps(question.answer_key) if question.answer_key else "")
        
        submitted = st.form_submit_button("Save Changes", use_container_width=True)
        
        if submitted:
            if not question_text:
                st.error("Question text is required!")
                return
            
            try:
                answer_key = json.loads(answer_key_text) if answer_key_text else {}
            except json.JSONDecodeError:
                st.error("Invalid JSON format for answer key!")
                return
            
            question.type = question_type
            question.question_text = question_text
            question.section_name = section_name if section_name else None
            question.sheet_template_url = sheet_template_url if sheet_template_url else None
            question.answer_key = answer_key
            question.points = points
            
            db.commit()
            
            st.success("Question updated!")
            st.rerun()

def import_questions_form(db, assessment_id):
    """Form to import questions from Google Sheet"""
    st.info("Import Questions feature - Enter Google Sheet URL with questions")
    sheet_url = st.text_input("Google Sheet URL", placeholder="https://docs.google.com/spreadsheets/d/...")
    
    if st.button("Import"):
        st.info("Question import feature requires Google Sheets API configuration. Coming soon!")

def invite_candidate(db, assessment_id, recruiter_id):
    """Invite a candidate to take an assessment"""
    st.subheader("Invite Candidate")
    
    with st.form("invite_candidate_form"):
        candidate_email = st.text_input("Candidate Email *")
        candidate_name = st.text_input("Candidate Name")
        
        submitted = st.form_submit_button("Send Invitation", use_container_width=True)
        
        if submitted:
            if not candidate_email:
                st.error("Email is required!")
                return
            
            # Generate unique token
            unique_token = str(uuid.uuid4())
            
            # Set expiration (1 year from now)
            expires_at = datetime.utcnow() + timedelta(days=365)
            
            invitation = Invitation(
                assessment_id=assessment_id,
                recruiter_id=recruiter_id,
                candidate_email=candidate_email,
                candidate_name=candidate_name,
                unique_token=unique_token,
                expires_at=expires_at,
                status='sent'
            )
            
            db.add(invitation)
            db.commit()
            
            # Generate invitation URL
            base_url = st.query_params.get('base_url', 'http://localhost:8501')
            invite_url = f"{base_url}?token={unique_token}"
            
            st.success(f"Invitation sent to {candidate_email}!")
            st.code(invite_url, language=None)
            st.info("Share this link with the candidate")

