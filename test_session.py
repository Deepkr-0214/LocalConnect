"""
Quick test script to verify session functionality
"""
from app import app, Customer, db
from flask import session

def test_session():
    with app.test_client() as client:
        with app.app_context():
            # Test customer login
            response = client.post('/signin', data={
                'role': 'customer',
                'username': 'test@example.com',
                'password': 'test123'
            }, follow_redirects=True)
            
            print(f"Login response status: {response.status_code}")
            print(f"Session data: {dict(session) if 'session' in locals() else 'No session'}")
            
            # Test accessing customer dashboard
            response = client.get('/customer/dashboard')
            print(f"Dashboard access status: {response.status_code}")

if __name__ == '__main__':
    test_session()