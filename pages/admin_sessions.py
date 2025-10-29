"""Admin Sessions Page"""

import streamlit as st
from datetime import datetime
from src.database import SessionLocal, Session, Assessment, Question, Response
from src.services.grading import GradingEngine

def render():
    st.title("👥 Sessions")
    
    db = SessionLocal()
    try:
        user_id = st.session_state.user['id']
        
        # Filter by assessment if selected
        assessment_filter = st.session_state.get('filter_assessment_id')
        
        if assessment_filter:
            st.info(f"Filtered by assessment")
            assessment = db.query(Assessment).filter(Assessment.id == assessment_filter).first()
            if assessment:
                st.subheader(f"Assessment: {assessment.title}")
        
        # Get sessions
        query = db.query(Session).join(Assessment).filter(Assessment.recruiter_id == user_id)
        
        if assessment_filter:
            query = query.filter(Session.assessment_id == assessment_filter)
        
        sessions = query.order_by(Session.created_at.desc()).all()
        
        if not sessions:
            st.info("No sessions found.")
            if assessment_filter:
                if st.button("← Back to All Sessions"):
                    del st.session_state.filter_assessment_id
                    st.rerun()
            return
        
        # Sessions list
        for session in sessions:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                
                with col1:
                    st.subheader(f"👤 {session.candidate_name or session.candidate_email}")
                    st.write(f"📝 Assessment: {session.assessment.title}")
                    if session.started_at:
                        st.caption(f"Started: {session.started_at.strftime('%Y-%m-%d %H:%M:%S')}")
                
                with col2:
                    status_color = {
                        'pending': 'gray',
                        'in_progress': 'blue',
                        'completed': 'green',
                        'expired': 'red'
                    }.get(session.status, 'gray')
                    st.markdown(f"**Status:** :{status_color}[{session.status}]")
                
                with col3:
                    if session.final_score is not None:
                        st.metric("Score", f"{session.final_score:.1f}")
                    else:
                        st.metric("Score", "N/A")
                
                with col4:
                    if session.suspicion_score > 0:
                        st.warning(f"⚠️ Suspicion: {session.suspicion_score}")
                
                # View details
                with st.expander("View Details"):
                    view_session_details(db, session)
                
                st.divider()
        
        if assessment_filter and st.button("← Back to All Sessions"):
            del st.session_state.filter_assessment_id
            st.rerun()
            
    finally:
        db.close()

def view_session_details(db, session):
    """View detailed information about a session"""
    st.write(f"**Email:** {session.candidate_email}")
    st.write(f"**Token:** {session.unique_token}")
    st.write(f"**IP Address:** {session.ip_address}")
    
    if session.completed_at:
        st.write(f"**Completed:** {session.completed_at.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Responses
    responses = db.query(Response).filter(Response.session_id == session.id).all()
    
    if responses:
        st.subheader("Responses")
        
        for response in responses:
            question = db.query(Question).filter(Question.id == response.question_id).first()
            if question:
                with st.expander(f"Question: {question.question_text[:50]}..."):
                    st.write(f"**Type:** {question.type}")
                    st.write(f"**Points:** {question.points}")
                    
                    if response.sheet_url:
                        st.write(f"**Sheet URL:** {response.sheet_url}")
                        st.link_button("Open Sheet", response.sheet_url)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Auto Score", f"{response.auto_score:.1f}" if response.auto_score else "N/A")
                    with col2:
                        st.metric("Manual Score", f"{response.manual_score:.1f}" if response.manual_score else "N/A")
                    
                    if response.reviewer_notes:
                        st.write(f"**Notes:** {response.reviewer_notes}")
                    
                    # Manual grading form
                    with st.form(f"grade_{response.id}"):
                        manual_score = st.number_input("Manual Score", 
                                                      min_value=0.0, 
                                                      max_value=float(question.points),
                                                      value=float(response.manual_score) if response.manual_score else 0.0,
                                                      key=f"manual_score_{response.id}")
                        reviewer_notes = st.text_area("Reviewer Notes", value=response.reviewer_notes or "")
                        
                        if st.form_submit_button("Update Score"):
                            response.manual_score = manual_score
                            response.reviewer_notes = reviewer_notes
                            response.graded_at = datetime.utcnow()
                            
                            # Recalculate final score
                            all_responses = db.query(Response).filter(Response.session_id == session.id).all()
                            total_points = sum([r.manual_score if r.manual_score else (r.auto_score if r.auto_score else 0) for r in all_responses])
                            session.final_score = total_points
                            
                            db.commit()
                            st.success("Score updated!")
                            st.rerun()
                    
                    # Re-grade button
                    if response.sheet_url and st.button("🔄 Re-grade", key=f"regrade_{response.id}"):
                        grading_engine = GradingEngine()
                        result = grading_engine.grade_response(question.__dict__, response.sheet_url)
                        
                        response.auto_score = result.get('auto_score', 0)
                        db.commit()
                        
                        st.success(f"Re-graded! Auto score: {result.get('auto_score', 0)}")
                        st.rerun()

