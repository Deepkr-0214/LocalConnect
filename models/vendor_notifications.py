from models.models import db
from datetime import datetime
import pytz

IST = pytz.timezone('Asia/Kolkata')

class VendorNotification(db.Model):
    __tablename__ = 'vendor_notification'
    
    id = db.Column(db.Integer, primary_key=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendor.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), nullable=False)  # 'new_order', 'payment', 'review', etc.
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(IST))
    order_id = db.Column(db.Integer, nullable=True)  # Link to specific order if applicable
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'type': self.type,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat(),
            'order_id': self.order_id,
            'time_ago': self.get_time_ago()
        }
    
    def get_time_ago(self):
        now = datetime.now(IST)
        diff = now - self.created_at
        
        if diff.days > 0:
            return f"{diff.days}d ago"
        elif diff.seconds > 3600:
            return f"{diff.seconds // 3600}h ago"
        elif diff.seconds > 60:
            return f"{diff.seconds // 60}m ago"
        else:
            return "Just now"