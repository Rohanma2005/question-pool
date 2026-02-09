from flask import session

def is_super_admin():
    """Check if current user is a super admin"""
    return session.get('role') == 'super_admin'

def is_faculty():
    """Check if current user is faculty"""
    return session.get('role') == 'faculty'

def get_current_user_id():
    """Get current logged-in user ID"""
    return session.get('user_id')
