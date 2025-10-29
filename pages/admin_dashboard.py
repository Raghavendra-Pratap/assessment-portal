"""Recruiter Dashboard Page"""

import streamlit as st
from datetime import datetime, timedelta
from src.database import SessionLocal, Assessment, Session, Question, Invitation, Response

def render():
    # Get user info
    user = st.session_state.get('user', {})
    user_name = user.get('name', 'User')
    
    # Welcome message
    st.title("Dashboard")
    st.markdown(f"**Welcome back, {user_name}!** Here's what's happening with your assessments today.")
    
    db = SessionLocal()
    try:
        user_id = st.session_state.user['id']
        
        # Get statistics
        total_assessments = db.query(Assessment).filter(Assessment.recruiter_id == user_id).count()
        
        # Total candidates (invitations sent)
        total_candidates = db.query(Invitation).join(Assessment).filter(
            Assessment.recruiter_id == user_id
        ).count()
        
        # In progress sessions
        in_progress = db.query(Session).join(Assessment).filter(
            Assessment.recruiter_id == user_id,
            Session.status == 'in_progress'
        ).count()
        
        # Completed sessions
        completed = db.query(Session).join(Assessment).filter(
            Assessment.recruiter_id == user_id,
            Session.status == 'completed'
        ).count()
        
        # Pending reviews (sessions with responses that need manual review)
        pending_reviews = db.query(Response).join(Session).join(Assessment).filter(
            Assessment.recruiter_id == user_id,
            Response.auto_score.isnot(None),
            Response.manual_score.is_(None)
        ).count()
        
        # Create Assessment button (top right)
        st.markdown("<br>", unsafe_allow_html=True)
        btn_col1, btn_col2 = st.columns([8, 2])
        with btn_col2:
            if st.button("Create Assessment", type="primary", use_container_width=True, key="create_btn_top"):
                st.session_state.page = 'assessments'
                st.session_state.create_new = True
                st.rerun()
        
        # Stats cards
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.markdown("""
            <div style="text-align: center; padding: 1.5rem; background: white; border-radius: 0.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <div style="font-size: 2rem; font-weight: 700; color: #2563eb;">{}</div>
                <div style="color: #6b7280; margin-top: 0.5rem;">Total Assessments</div>
            </div>
            """.format(total_assessments), unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div style="text-align: center; padding: 1.5rem; background: white; border-radius: 0.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <div style="font-size: 2rem; font-weight: 700; color: #2563eb;">{}</div>
                <div style="color: #6b7280; margin-top: 0.5rem;">Total Candidates</div>
            </div>
            """.format(total_candidates), unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div style="text-align: center; padding: 1.5rem; background: white; border-radius: 0.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <div style="font-size: 2rem; font-weight: 700; color: #2563eb;">{}</div>
                <div style="color: #6b7280; margin-top: 0.5rem;">In Progress</div>
            </div>
            """.format(in_progress), unsafe_allow_html=True)
        
        with col4:
            st.markdown("""
            <div style="text-align: center; padding: 1.5rem; background: white; border-radius: 0.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <div style="font-size: 2rem; font-weight: 700; color: #2563eb;">{}</div>
                <div style="color: #6b7280; margin-top: 0.5rem;">Completed</div>
            </div>
            """.format(completed), unsafe_allow_html=True)
        
        with col5:
            st.markdown("""
            <div style="text-align: center; padding: 1.5rem; background: white; border-radius: 0.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <div style="font-size: 2rem; font-weight: 700; color: #2563eb;">{}</div>
                <div style="color: #6b7280; margin-top: 0.5rem;">Pending Reviews</div>
            </div>
            """.format(pending_reviews), unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Recent Assessments section
        st.markdown("### Recent Assessments")
        
        # Get recent assessments
        recent_assessments = db.query(Assessment).filter(
            Assessment.recruiter_id == user_id
        ).order_by(Assessment.created_at.desc()).limit(10).all()
        
        if recent_assessments:
            # Create table data
            table_data = []
            for assessment in recent_assessments:
                # Get question count
                question_count = db.query(Question).filter(Question.assessment_id == assessment.id).count()
                
                # Get candidate count
                candidate_count = db.query(Invitation).filter(Invitation.assessment_id == assessment.id).count()
                
                # Get completed count
                completed_count = db.query(Session).filter(
                    Session.assessment_id == assessment.id,
                    Session.status == 'completed'
                ).count()
                
                # Get status (simplified - can be enhanced)
                status = "Draft" if question_count == 0 else "Active"
                
                table_data.append({
                    "Title": assessment.title,
                    "Subtitle": assessment.description[:50] + "..." if assessment.description and len(assessment.description) > 50 else (assessment.description or "Assessment created via form"),
                    "Status": status,
                    "Questions": question_count,
                    "Candidates": candidate_count,
                    "Completed": completed_count,
                    "Created": assessment.created_at.strftime('%b %d, %Y') if assessment.created_at else "N/A",
                    "Assessment ID": assessment.id
                })
            
            # Display as table with custom styling
            for assessment_data in table_data:
                with st.container():
                    col1, col2, col3, col4, col5, col6, col7 = st.columns([3, 1.5, 1, 1, 1, 1.5, 2])
                    
                    with col1:
                        st.markdown(f"**{assessment_data['Title']}**")
                        st.caption(assessment_data['Subtitle'])
                    
                    with col2:
                        # Status badge
                        status_color = "#2563eb" if assessment_data['Status'] == 'Draft' else "#10b981"
                        st.markdown(f"""
                        <div style="display: inline-block; padding: 0.25rem 0.75rem; border-radius: 9999px; background: #eff6ff; color: {status_color}; font-size: 0.875rem; font-weight: 500;">
                            {assessment_data['Status']}
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col3:
                        st.write(assessment_data['Questions'])
                    with col4:
                        st.write(assessment_data['Candidates'])
                    with col5:
                        st.write(assessment_data['Completed'])
                    with col6:
                        st.write(assessment_data['Created'])
                    
                    with col7:
                        action_col1, action_col2, action_col3 = st.columns(3)
                        with action_col1:
                            if st.button("Edit", key=f"edit_{assessment_data['Assessment ID']}", use_container_width=True):
                                st.session_state.edit_assessment_id = assessment_data['Assessment ID']
                                st.session_state.page = 'assessments'
                                st.rerun()
                        with action_col2:
                            if st.button("Invite", key=f"invite_{assessment_data['Assessment ID']}", type="primary", use_container_width=True):
                                st.session_state.invite_assessment_id = assessment_data['Assessment ID']
                                st.session_state.page = 'assessments'
                                st.rerun()
                        with action_col3:
                            if st.button("View", key=f"view_{assessment_data['Assessment ID']}", use_container_width=True):
                                st.session_state.view_assessment_id = assessment_data['Assessment ID']
                                st.session_state.page = 'assessments'
                                st.rerun()
                    
                    st.divider()
        else:
            st.info("No assessments found. Create your first assessment to get started!")
            
    finally:
        db.close()
