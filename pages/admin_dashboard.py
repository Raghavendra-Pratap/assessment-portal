"""Admin Dashboard Page"""

import streamlit as st
from datetime import datetime, timedelta
from src.database import SessionLocal, Assessment, Session, Question

def render():
    st.title("📊 Dashboard")
    
    db = SessionLocal()
    try:
        user_id = st.session_state.user['id']
        
        # Get statistics
        total_assessments = db.query(Assessment).filter(Assessment.recruiter_id == user_id).count()
        total_sessions = db.query(Session).join(Assessment).filter(Assessment.recruiter_id == user_id).count()
        completed_sessions = db.query(Session).join(Assessment).filter(
            Assessment.recruiter_id == user_id,
            Session.status == 'completed'
        ).count()
        
        # Recent assessments
        recent_assessments = db.query(Assessment).filter(
            Assessment.recruiter_id == user_id
        ).order_by(Assessment.created_at.desc()).limit(5).all()
        
        # Recent sessions
        recent_sessions = db.query(Session).join(Assessment).filter(
            Assessment.recruiter_id == user_id
        ).order_by(Session.created_at.desc()).limit(10).all()
        
        # Stats columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Assessments", total_assessments)
        with col2:
            st.metric("Total Sessions", total_sessions)
        with col3:
            st.metric("Completed", completed_sessions)
        with col4:
            completion_rate = (completed_sessions / total_sessions * 100) if total_sessions > 0 else 0
            st.metric("Completion Rate", f"{completion_rate:.1f}%")
        
        st.divider()
        
        # Recent assessments
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Recent Assessments")
            if recent_assessments:
                for assessment in recent_assessments:
                    with st.expander(f"📝 {assessment.title}", expanded=False):
                        st.write(f"**Duration:** {assessment.duration_minutes} minutes")
                        st.write(f"**Created:** {assessment.created_at.strftime('%Y-%m-%d %H:%M')}")
                        if assessment.description:
                            st.write(f"**Description:** {assessment.description[:100]}...")
                        
                        col_a, col_b = st.columns(2)
                        with col_a:
                            if st.button(f"Edit", key=f"edit_{assessment.id}"):
                                st.session_state.edit_assessment_id = assessment.id
                                st.session_state.page = 'assessments'
                                st.rerun()
                        with col_b:
                            if st.button(f"View Sessions", key=f"sessions_{assessment.id}"):
                                st.session_state.filter_assessment_id = assessment.id
                                st.session_state.page = 'sessions'
                                st.rerun()
            else:
                st.info("No assessments yet. Create your first assessment!")
        
        with col2:
            st.subheader("Quick Actions")
            if st.button("➕ Create Assessment", use_container_width=True, type="primary"):
                st.session_state.page = 'assessments'
                st.session_state.create_new = True
                st.rerun()
            if st.button("📥 Import Questions", use_container_width=True):
                st.info("Import feature coming soon!")
            
        st.divider()
        
        # Recent sessions
        st.subheader("Recent Sessions")
        if recent_sessions:
            sessions_data = []
            for session in recent_sessions:
                sessions_data.append({
                    "Candidate": session.candidate_name or session.candidate_email,
                    "Assessment": session.assessment.title,
                    "Status": session.status,
                    "Score": f"{session.final_score:.1f}" if session.final_score else "N/A",
                    "Started": session.started_at.strftime('%Y-%m-%d %H:%M') if session.started_at else "N/A"
                })
            st.dataframe(sessions_data, use_container_width=True, hide_index=True)
        else:
            st.info("No sessions yet.")
            
    finally:
        db.close()

