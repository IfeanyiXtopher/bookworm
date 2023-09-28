from flask import Flask
from flask_wtf.csrf import CSRFProtect

from flask_migrate import Migrate
from flask_mail import Mail,Message

csrf=CSRFProtect()
mail=Mail()

def create_app():
    """keepall import that may cause conflict within this 
        function so that anytime we write "from pkg.. imort.. none of these statments will be executed"""
    from bookapp.models import db
    app=Flask(__name__,instance_relative_config=True)#this instance_relative_config is b/c we moved our config to instance folder.
    app.config.from_pyfile('config.py')
    db.init_app(app)
    migrate = Migrate(app,db)
    csrf.init_app(app)
    mail.__init__(app)
    return app


#Instantiate an object of Flask so that it can be easily imported by other modules inthe package
app = create_app()


#load the route here
from bookapp import admin_routes, user_routes

#load the models, form
from bookapp.forms import *