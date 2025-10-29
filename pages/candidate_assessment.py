"""Candidate Assessment Page"""

import streamlit as st
import uuid
from datetime import datetime, timedelta
from src.database import SessionLocal, Invitation, Session, Assessment, Question, Response
from src.services.google_sheets import get_google_sheets_service

def render():
    query_params = st.query_params
    token = query_params.get('token', '')
    
    if not token:
        st.error("Invalid assessment link. No token provided.")
        return
    
    db = SessionLocal()
    try:
        # Validate invitation
        invitation = db.query(Invitation).filter(Invitation.unique_token == token).first()
        
        if not invitation:
            st.error("Invalid or expired assessment link.")
            return
        
        if invitation.expires_at < datetime.utcnow():
            st.error("This assessment link has expired.")
            return
        
        if invitation.status == 'completed':
            st.success("You have already completed this assessment.")
            st.info("Assessment completed successfully!")
            return
        
        # Get assessment
        assessment = db.query(Assessment).filter(Assessment.id == invitation.assessment_id).first()
        
        if not assessment:
            st.error("Assessment not found.")
            return
        
        # Check if session exists
        session = db.query(Session).filter(Session.unique_token == token).first()
        
        if not session:
            # Show consent form
            show_consent_form(db, invitation, assessment, token)
        else:
            # Show assessment interface
            show_assessment_interface(db, session, assessment)
            
    finally:
        db.close()

def show_consent_form(db, invitation, assessment, token):
    """Show consent and information form before starting assessment"""
    st.title("📊 Excel Assessment")
    st.markdown(f"### {assessment.title}")
    
    if assessment.description:
        st.info(assessment.description)
    
    st.write(f"**Duration:** {assessment.duration_minutes} minutes")
    st.write(f"**Candidate:** {invitation.candidate_name or invitation.candidate_email}")
    
    st.divider()
    
    st.subheader("Assessment Consent")
    st.write("Before starting the assessment, please review and accept the following:")
    
    # Consent checkboxes
    consent_webcam = st.checkbox("I consent to webcam recording during the assessment", value=False)
    consent_screen = st.checkbox("I consent to screen capture during the assessment", value=False)
    consent_monitoring = st.checkbox("I understand that my activity will be monitored for integrity", value=False)
    consent_rules = st.checkbox("I agree to follow all assessment rules and guidelines", value=False)
    
    if invitation.google_email:
        st.success(f"✓ Verified: {invitation.google_email}")
    else:
        st.warning("⚠️ Google Sign-in recommended for verification")
        if st.button("Sign in with Google"):
            st.info("Google OAuth integration - Coming soon!")
    
    if st.button("Start Assessment", type="primary", use_container_width=True, 
                disabled=not (consent_webcam and consent_screen and consent_monitoring and consent_rules)):
        if not all([consent_webcam, consent_screen, consent_monitoring, consent_rules]):
            st.error("Please accept all consent terms to proceed.")
            return
        
        # Create session
        session = Session(
            assessment_id=assessment.id,
            candidate_name=invitation.candidate_name or invitation.candidate_email,
            candidate_email=invitation.candidate_email,
            unique_token=token,
            started_at=datetime.utcnow(),
            status='in_progress',
            ip_address=get_client_ip()
        )
        
        db.add(session)
        
        # Update invitation status
        invitation.status = 'started'
        
        db.commit()
        
        st.rerun()

def show_assessment_interface(db, session, assessment):
    """Show the actual assessment interface"""
    # Get questions
    questions = db.query(Question).filter(Question.assessment_id == assessment.id).order_by(Question.display_order).all()
    
    if not questions:
        st.error("No questions found for this assessment.")
        return
    
    # Check if already completed
    if session.status == 'completed':
        show_completion_screen(db, session, assessment)
        return
    
    # Timer
    if session.started_at:
        elapsed = (datetime.utcnow() - session.started_at).total_seconds() / 60
        remaining = assessment.duration_minutes - elapsed
        
        if remaining <= 0:
            # Time's up - auto-submit
            submit_assessment(db, session)
            st.rerun()
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.title(f"📊 {assessment.title}")
        with col2:
            st.metric("Time Remaining", f"{int(remaining)} min")
    
    # Question navigation
    if 'current_question_idx' not in st.session_state:
        st.session_state.current_question_idx = 0
    
    current_idx = st.session_state.current_question_idx
    
    # Question tabs
    question_tabs = [f"Q{i+1}" for i in range(len(questions))]
    tabs = st.tabs(question_tabs)
    
    for idx, (question, tab) in enumerate(zip(questions, tabs)):
        with tab:
            display_question(db, session, question, idx)
    
    st.divider()
    
    # Navigation and Submit
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("◀ Previous", disabled=current_idx == 0):
            st.session_state.current_question_idx = max(0, current_idx - 1)
            st.rerun()
    
    with col2:
        st.write(f"Question {current_idx + 1} of {len(questions)}")
    
    with col3:
        if st.button("Next ▶", disabled=current_idx >= len(questions) - 1):
            st.session_state.current_question_idx = min(len(questions) - 1, current_idx + 1)
            st.rerun()
    
    st.divider()
    
    # Submit button
    if st.button("Submit Assessment", type="primary", use_container_width=True):
        if st.checkbox("I confirm that I want to submit my assessment"):
            submit_assessment(db, session)
            st.rerun()

def display_question(db, session, question, question_idx):
    """Display a question and handle responses"""
    st.subheader(f"Question {question_idx + 1}: {question.type.upper()}")
    
    if question.section_name:
        st.caption(f"Section: {question.section_name}")
    
    st.write(f"**Points:** {question.points}")
    st.write(question.question_text)
    
    # Check if response exists
    response = db.query(Response).filter(
        Response.session_id == session.id,
        Response.question_id == question.id
    ).first()
    
    google_sheets = get_google_sheets_service()
    
    if question.type in ['formula', 'data-entry', 'scenario']:
        # Google Sheet interface
        if question.sheet_template_url:
            st.subheader("Your Work Sheet")
            
            # Copy template if not already done
            if not response or not response.sheet_url:
                if google_sheets:
                    sheet_id = google_sheets.extract_sheet_id(question.sheet_template_url)
                    if sheet_id:
                        if st.button(f"Create Your Copy", key=f"copy_{question.id}"):
                            copy_result = google_sheets.copy_sheet(
                                sheet_id,
                                f"{assessment.title} - Q{question_idx + 1} - {session.candidate_email}",
                                session.candidate_email
                            )
                            
                            if copy_result.get('success'):
                                # Save response
                                if not response:
                                    response = Response(
                                        session_id=session.id,
                                        question_id=question.id,
                                        sheet_url=copy_result['url']
                                    )
                                    db.add(response)
                                else:
                                    response.sheet_url = copy_result['url']
                                
                                db.commit()
                                st.success("Sheet copied! You can now work on your assessment.")
                                st.rerun()
                            else:
                                st.error(f"Error copying sheet: {copy_result.get('error')}")
                
                st.info("Click the button above to create your copy of the template sheet.")
            
            # Show embedded sheet
            if response and response.sheet_url:
                st.link_button("Open Your Sheet in Google Sheets", response.sheet_url)
                
                # Show sheet link (iframe embedding requires additional setup)
                st.info(f"📊 Work on your assessment in the Google Sheet linked above.")
                st.caption("The sheet will be automatically graded when you submit your assessment.")
    
    elif question.type == 'mcq':
        # Multiple choice question
        st.write("**Select your answer:**")
        
        # For now, simple text input (could be enhanced with radio buttons)
        answer_text = st.text_input("Your Answer (A, B, C, or D)", 
                                   value=response.sheet_url if response else "",
                                   key=f"mcq_{question.id}")
        
        if answer_text and st.button("Save Answer", key=f"save_mcq_{question.id}"):
            if not response:
                response = Response(
                    session_id=session.id,
                    question_id=question.id,
                    sheet_url=answer_text  # Store answer in sheet_url for MCQ
                )
                db.add(response)
            else:
                response.sheet_url = answer_text
            
            db.commit()
            st.success("Answer saved!")

def submit_assessment(db, session):
    """Submit and grade the assessment"""
    # Get all responses
    responses = db.query(Response).filter(Response.session_id == session.id).all()
    
    from src.services.grading import GradingEngine
    grading_engine = GradingEngine()
    
    total_score = 0
    
    for response in responses:
        question = db.query(Question).filter(Question.id == response.question_id).first()
        if question and response.sheet_url:
            # Grade the response
            result = grading_engine.grade_response(question.__dict__, response.sheet_url)
            
            response.auto_score = result.get('auto_score', 0)
            total_score += result.get('auto_score', 0)
        
        db.commit()
    
    # Update session
    session.status = 'completed'
    session.completed_at = datetime.utcnow()
    session.final_score = total_score
    
    # Update invitation
    invitation = db.query(Invitation).filter(Invitation.unique_token == session.unique_token).first()
    if invitation:
        invitation.status = 'completed'
        invitation.completed_at = datetime.utcnow()
    
    db.commit()

def show_completion_screen(db, session, assessment):
    """Show completion screen after submission"""
    st.title("✅ Assessment Completed!")
    st.success("Thank you for completing the assessment.")
    
    st.subheader("Your Score")
    if session.final_score is not None:
        # Calculate total possible points
        questions = db.query(Question).filter(Question.assessment_id == assessment.id).all()
        total_points = sum([q.points for q in questions])
        
        percentage = (session.final_score / total_points * 100) if total_points > 0 else 0
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Your Score", f"{session.final_score:.1f} / {total_points:.1f}")
        with col2:
            st.metric("Percentage", f"{percentage:.1f}%")
    
    st.info("Results will be reviewed and you will be notified once grading is complete.")

def get_client_ip():
    """Get client IP address"""
    # Simplified - in production, get from request headers
    return "127.0.0.1"

