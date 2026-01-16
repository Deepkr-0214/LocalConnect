import os

class Config:
    SECRET_KEY = 'dev_key_localconnect' # Change this later
    # Use parent directory's database to share with customer module
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(os.path.dirname(os.getcwd()), "instance", "database.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
