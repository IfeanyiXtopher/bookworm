import json, requests, random, string

from functools import wraps
from flask import render_template, request, abort, redirect, flash,make_response, url_for,session

from werkzeug.security import generate_password_hash, check_password_hash

#Local imports
from bookapp import app, csrf, mail, Message
from bookapp.models import db, Book, User, Category, State, Lga, Reviews, Donation
from bookapp.forms import *

def generate_string(howmany):#call this function as gererate_string(10)
    x = random.sample(string.ascii_lowercase,howmany)
    return ''.join(x)

@app.route("/sendmail/")
def send_mail():
    file=open('requirements.txt')
    msg = Message(subject="Adding headers", sender='From Bookworm',recipient=['nwagbaraxtopher@gmail.com'],body="Thank you for contacting us")
    msg.html= """<h1 class='text-center'>Thank you For Contacting us</h1> </div>"""
    msg.attch('save_as.txt','application/text',file.read())
    mail.send(msg)
    return "done"

def login_required(f):
    @wraps(f)#this ensures that details(meta data) about the original function f, that is being decorated is still available ### we wont be needing to check if session.get('userloggedin') == None or session.get('role') != "admin"
    def login_check(*args,**kwargs):
        if session.get("userloggedin") != None:
            return f(*args,**kwargs)
        else:
            flash("Access denied")
            return redirect('/login')
    return login_check 
#To use login_required, place it after the route decorator over any route that needs authentication


@app.route("/ajaxopt/",methods=['GET',"POST"])
def ajax_options():
    cform = ContactForm()
    if request.method=='GET':
        return render_template("user/ajax_options.html", cform=cform)
    else:
        email = request.form.get('email')# the name attribute of the form input b/c we used either form.serialize or forData 
        return "Form has been submitted"



@app.route('/initialize/paystack/')
@login_required
def initialize_paystack():
    deets=User.query.get(session['userloggedin'])
    refno=session.get('trxno')
    transaction_deets=db.session.query(Donation).filter(Donation.don_refno==refno).first()
    url="https://api.paystack.co/transaction/initialize"
    headers={"Content-Type": "application/json","Authorization": "Bearer sk_test_2473b2cdabb44925d750849f4a658f47f03f5ef7"}
    data={ "email": deets.user_email, "amount":transaction_deets.don_amt, "reference":refno}
    response=requests.post(url,headers=headers,data=json.dumps(data))
    rspjson=response.json()
    # return rspjson
    if rspjson['status']==True:
        redirectURL=rspjson['data']['authorization_url']
        return redirect(redirectURL) #paystack payment page will load
    else:
        flash('please complete the form again')
        return redirect('/donate')

@app.route('/landing')
@login_required
def landing_page():
    refno=session.get('trxno')
    transaction_deets=db.session.query(Donation).filter(Donation.don_refno==refno).first()
    url='https://api.paystack.co/transaction/verify/'+transaction_deets.don_refno
    headers={"Content-Type": "application/json","Authorization": "Bearer sk_test_2473b2cdabb44925d750849f4a658f47f03f5ef7"}
    response=requests.get(url,headers=headers)
    rspjson=json.loads(response.text)
    if rspjson['status']==True:
        paystatus=rspjson['data']['gateway_response']
        transaction_deets.don_status='Paid'
        db.session.commit()
        return redirect('/dashboard')
    else:
        flash('Payment failed')
        return redirect('/reports')
    

@app.route('/donate/', methods=["POST","GET"])
@login_required
def donate():
    if request.method=="GET":
        deets=db.session.query(User).get(session['userloggedin'])
        return render_template('user/donate.html',deets=deets)
    else:
        fname=request.form.get('fullname')
        email=request.form.get('email')
        amount= float(request.form.get('amt')) * 100 
        ref='BW/'+str(generate_string(8))
        donation = Donation(don_amt=amount,don_email=email,don_fullname=fname,don_userid=session['userloggedin'],don_status='pending',don_refno=ref)
        db.session.add(donation)
        db.session.commit()
        session['trxno']=ref #to save refrence no in session
        #redirect to a confirmaation page
        return redirect('/confirm_donation')
    
        
@app.route('/confirm_donation/')
@login_required
def confirm_donation():
    '''We want to display transaction saved from previous page'''
    deets=db.session.query(User).get(session['userloggedin'])
    if session.get('trxno')==None: #when visited directly
        flash('please complete the form', category='error')
        return redirect('/donate')
    else:
        donation_deets=Donation.query.filter(Donation.don_refno==session['trxno']).first()
        return render_template('user/donation_confirmation.html',donation_deets=donation_deets,deets=deets)



@app.route("/dependent/")
def dependent_dropdown():
    states = db.session.query(State).all()
    return render_template("user/show_state.html",states=states)

@app.route('/lga/<stateid>')
def load_lgas(stateid):
    records=db.session.query(Lga).filter(Lga.state_id==stateid).all()
    str2return='<select class="form-control" name="lga">'
    for r in records:
        optstr=f"<option value='{r.lga_id}'>"+r.lga_name+"</option>"
        str2return = str2return + optstr
    str2return=str2return +'</select>'
    return str2return


@app.route("/contact/")
def ajax_contact():
    data = "I am a string coming from server" #this can be fatch from db
    return render_template("user/ajax_test.html", data=data)

@app.route("/submission/", methods=["get","post"])
def ajax_submission():
    """This route will be visited by ajax silently"""
    user = request.form.get('fullname')
    if user != "" and user != None:
        return f"Thnak you {user} for completing the form"
    else:
        return "Please complete the form" #This can also be fated from db

@app.route('/checkusername/',methods=['post','get'])
def checkusername():
    mail=request.form.get('usermail')
    check = db.session.query(User).filter(User.user_email==mail).first()

    if check:
        return "Email has been taken"
    else:
        return "Email is Okay, go ahead"


@app.route("/favourite")
def favourite_topics():
    bootcamp = {'name':'Olusegun','topics':['html','css','python']}
    category=[]         #[c.cat_name in Category]
    cats = db.session.query(Category).all()
    for c in cats:
        category.append(c.cat_name)
    
    return json.dumps(category)


@app.route("/changedp/", methods=["GET","POST"])
@login_required
def changedp():
    id = session.get('userloggedin')
    userdeets = db.session.query(User).get(id)
    dpform = DpForm()
    if request.method == 'GET':
        return render_template("user/changedp.html",dpform=dpform, userdeets=userdeets)
    else:#form is being submitted
        if dpform.validate_on_submit():
            pix = request.files.get('dp')
            filename = pix.filename
            pix.save(app.config['USER_PROFILE_PATH']+filename)
            userdeets.user_pix = filename
            db.session.commit()
            flash("Profile picture updated")
            return redirect(url_for('dashboard'))
        else:
            return render_template("user/changedp.html", dpform=dpform, userdeets=userdeets)


@app.route("/profile", methods=["POST","GET"])
@login_required
def edit_profile():
    id = session.get("userloggedin")
    userdeets = db.session.query(User).get(id)
    pform = ProfileForm()
    if request.method =='GET':
        return render_template('user/edit_profile.html', pform=pform, userdeets=userdeets)
    else:
        if pform.validate_on_submit():
            fullname = request.form.get('fullname') #OR pform.fullname.data
            userdeets.user_fullname = fullname
            db.session.commit()
            flash("Profile Updated")
            return redirect('/dashboard')
        else:
            return render_template('user/edit_profile.html', pform=pform, userdeets=userdeets)


@app.route("/viewall/")
def viewall():
    books = db.session.query(Book).filter(Book.book_status=='1').all()
    return render_template("user/viewall.html",books=books)

@app.route("/logout")
def logout():
    if session.get('userloggedin') != None:
        session.pop("userloggedin", None)
    return redirect('/')

@app.route("/dashboard")
def dashboard():
    if session.get('userloggedin') != None:
        id = session.get('userloggedin')
        userdeets = User.query.get(id)
        return render_template("user/dashboard.html", userdeets=userdeets)
    else:
        flash("you need to login to access this page")
        return redirect("/login")


@app.route('/login', methods = ["POST","GET"])
def login():
    if request.method == "GET":
        return render_template('user/loginpage.html')
    else: 
        #etrieve form data
        email = request.form.get('email')
        pwd = request.form.get('pwd')

        deets = db.session.query(User).filter(User.user_email==email).first()
        if deets != None:
            hashed_pwd = deets.user_pwd
            if check_password_hash(hashed_pwd,pwd) == True:
                session['userloggedin'] = deets.user_id
                return redirect("/dashboard")
            else:
                flash("Invalid credentials, try again")
                return redirect("/login")
        else:
            flash("Invalid credentials, try again")
            return redirect("/login")


@app.route("/register/", methods=["GET","POST"])
def register():
    regform = RegForm()
    if request.method == "GET":
        return render_template("user/signup.html", regform=regform)
    else:
        if regform.validate_on_submit(): #retrieve from data
            fullname = request.form.get('fullname') #OR regform.fullname.data
            email = request.form.get('email') #OR regform.email.data
            pwd = request.form.get('pwd')
            hashed_pwd = generate_password_hash(pwd)
            u = User(user_fullname=fullname,user_email=email,user_pwd=hashed_pwd)
            db.session.add(u)
            db.session.commit()

            flash("Account created please login")
            return redirect('/login')
        else:
            return render_template("user/signup.html", regform=regform) #while using flaskform dont redirect (you will loose the messages)

@app.route("/")
def home_page():
    books = db.session.query(Book).filter(Book.book_status == "1").limit(4).all()
    #return render_template("user/home_page.html", books=books)
    #connect to the endpoint http://127.0.0.1:5000/api/v0.1/listall to collect data of books
    #pass it to the template and display on the template
    try:
        response = request.get('http://127.0.0.1:5000/api/v1.0/listall') #import request
        rsp = json.load(response) #or response.json()
    except:
        rsp = None #if the server is unreacheble

    return render_template('user/home_page.html',books=books,rsp=rsp)


@app.route("/submit_review/", methods=["POST"])# No get b/c i dont want people to visit it directly
@login_required
def  submit_review():
    #retrieve and send to db
    title = request.form.get('title')
    content = request.form.get('content')
    book = request.form.get('book')
    userid = session['userloggedin']

    revs = Reviews(rev_title=title,rev_text=content, rev_bookid=book, rev_userid=userid)
    db.session.add(revs)
    db.session.commit()

    retstr= f"""<article class="blog-post">
        <h5 class="blog-post-title">{title}</h5>
        <p class="blog-post-meta">reviewed just now by<a href="#">{ revs.reviewby.user_fullname }</a></p>

        <p>{ content }</p>
        <hr> 
        </article>"""
    return retstr


@app.route("/myreviews")
@login_required
def myreviews():
    id = session['userloggedin']
    userdeets = db.session.query(User).get(id)

    return render_template("user/myreviews.html", userdeets=userdeets)
    

@app.route("/books/details/<int:id>")
def book_details(id):
    book = Book.query.get_or_404(id) #
    return render_template("user/reviews.html", book=book)


@app.after_request
def after_request(response):
    #To solve the problem of loggedout user's details being cached in the browser
    response.headers["Cache-Control"] = "no-catche, no-store, must-revalidate"
    return response 