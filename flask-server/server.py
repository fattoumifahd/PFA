# import mysql.connector
from flask import Flask , jsonify , request , session, url_for
from flask_cors import CORS 
from model import Users , OrderItem , MenuItems , Reservations , Orders , Compus ,  db
from itsdangerous import URLSafeSerializer , SignatureExpired
from flask_marshmallow import Marshmallow
from datetime import datetime
import redis
from flask_bcrypt import Bcrypt
from flask_session import Session
from flask_mail import Mail , Message
import string
import random
import os




# # connect to database

# db = mysql.connector.connect (
#     host= "localhost",
#     user= "root",
#     password= "",
#     database= "restaurant"
# )

# cur = db.cursor()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root@localhost/resto'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHRMY_ECHO'] = True
app.config['SESSION_TYPE'] = "redis"
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_REDIS'] = redis.from_url('redis://127.0.0.1:6379')

app.config["MAIL_SERVER"] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'fahdfattoumi8@gmail.com'
app.config['MAIL_PASSWORD'] = 'htep xcht svbb yhun'
app.config['MAIL_USE_TL5'] = False
app.config['MAIL_USE_SSL'] = True

mail = Mail(app)
cors = CORS(app, resources={r"/http://localhost:3000/*": {"origins": "*"}})
app.secret_key = 'secret key'

server_session = Session(app)

s = URLSafeSerializer('secret key')





db.init_app(app)
ma = Marshmallow(app)
app.app_context().push()    
bcrypt = Bcrypt(app)


# session(app)

# users Schema
class userSchema(ma.Schema):
    class Meta:
        fields = ('user_id','nom' , 'prenom' , 'email', 'password')
user_shema = userSchema(many=True)


# Menu_items Schema
class Menu_items_Schema(ma.Schema):
    class Meta:
        fields = ('item_id','nom' , 'description', 'prix' , 'categorie', 'image')
menu_items_shema = Menu_items_Schema(many=True)

#compus Schema 
class Compus_Schema(ma.Schema):
    class Meta:
        fields = ('compus_id','place' , 'telephone', 'ville' )
compus_schema = Compus_Schema(many=True)

class Reservations_Schema(ma.Schema):
    class Meta : 
        fields = ('id', 'order_id', 'user_id', 'compus_id', "invite", "payment")
reservation_shema = Reservations_Schema(many=True)


@app.route('/')
def index():
    res = Users.query.all()
    users = user_shema.dump(res)
    return jsonify(users) 


@app.route('/menuItems')
def menuItems():
    res = MenuItems.query.all()
    menu_items = menu_items_shema.dump(res)
    return jsonify(menu_items)


@app.route("/signup", methods=["POST"])
def signup():
    if request.method == "POST":
        data = request.json
        email = data['email']
        hash_password = bcrypt.generate_password_hash(data['password'])
        newUser =  Users(data['nom'], data['prenom'], data['email'] , hash_password, data['tele'])
        db.session.add(newUser)
        db.session.flush()
        # token = s.dumps(email , salt='email-verification')
        mes = Message("EMAIL VERFICATION" , recipients=[email], sender='fahdfattoumi8@gmail.com')
        
        link = url_for('email_verification' , user_id=newUser.user_id , _external=True)
        mes.body= "HI THEIR PLEACE VERIFY YOU EMAIL BY TO LINK BELLOW \n {}".format(link)
        mail.send(mes)
        db.session.commit()
        
        return {"messege" : "ok"}
    
@app.route('/email_verification/<user_id>')
def email_verification(user_id):
    user = Users.query.filter_by(user_id=user_id).update({'mail_verification' : 1})
    db.session.commit()
    # print(user.nom)
    print(user)
    return "email verified"
    



@app.route('/users', methods=['GET'])
def users(): 
    if request.method == "GET":
        res = Users.query.all()
        print(res)
        emails = user_shema.dump(res)
        return emails
        

@app.route('/menuItems/<categorie>', methods=['GET'])
def Menu_Items(categorie):
    if request.method == "GET":
        res = MenuItems.query.filter_by(categorie = categorie)
        items = menu_items_shema.dump(res)
#         cur = db.cursor()
#         cur.execute("select * from MenuItems where categorie=%s",(categorie,))
#         rows = cur.fetchall()
#         data = get_array_objct(rows , cur.column_names)
    return items


@app.route('/api/login' , methods=["GET","POST"]) 
def login() :
    if request.method == "GET":
        # print()
        # if session['user']  None :
        try:
            return {'user' : session['user']}
        except KeyError:
            return {'user' : None}
        except:
            return "something get wrong"
        # else :
            # return {'user' : None}
    else: 
        # res = Users.query.filter_by(email = request.json['email'] , password = request.json['password']).one()
        email = request.json['email']
        password = request.json['password']
        user = db.session.query(Users).filter_by(email = email).first()
        # user = user_shema.dump(res)
        print(user)
        if user is  None :
            return {"user" : None}
        elif not bcrypt.check_password_hash(user.password , password):
                return {"user" : None}
        else: 
            user_login = {
                "user_id" : user.user_id,
                "nom": user.nom,
                "prenom": user.prenom,
                "email": user.email,
                "password": user.password,
                "tele": user.telephone
                
            }
            session['user'] = user_login
            return  {"user" : user_login}
        

@app.route('/compus')
def compus():
    res = Compus.query.all()
    compus = compus_schema.dump(res)
    print(compus)
    return  compus



        
@app.route("/api/logout")
def logout() :
    session.pop('user')
    return {'user' : None}
    

    
@app.route('/add_order' ,methods=['POST'])
def add_order():
    if request.method == "POST":
        data = request.get_json()
        print(data)
        items = data['basket']
        new_order = Orders(user_id=data['user_id'] , prix_total=data['total'])
        db.session.add(new_order)
        db.session.flush()
        
        
        print(data['quantite'])
        print('-------------\n')
        
        for item in items:
            id = str(item['item_id'])
            new_order_item = OrderItem(order_id=new_order.order_id, item_id = item['item_id'], quantity=data['quantite'][id])
            # print(item['item_id'])
            # print(data['quantite'][id])
            db.session.add(new_order_item)
        
        db.session.commit()
        
        return {'message' : "ok"}
    
    
@app.route('/forget_pass', methods=["POST"])
def forgetPass():
    if request.method == "POST":
        email = request.json['email']
        print(email)
        all_charactere = string.ascii_letters + string.digits + string.punctuation
        new_pass = "".join(random.choices(all_charactere , k = 12))
        print (new_pass)
        new_pass_hash = bcrypt.generate_password_hash(new_pass)
        Users.query.filter_by(email=email).update({"password" : new_pass_hash})
        db.session.commit()
        msg = Message("mot de pass oublie" ,recipients=[email] , sender='fahdfattoumi8@gmail.com')
        msg.body = "We regenerate a new password for you \n new password :  {}".format(new_pass)
        mail.send(msg)
        
        
        # msg.body = ""
        return {"message":"ok"}
    
@app.route("/admin/resevations" , methods=["POST", "GET"])
def reservations():
    if request.method == "GET":
        
        res = Reservations.query.all()
        reservations = reservation_shema.dump(res)
        return {"reservations" : reservations}
    
    


if __name__ == '__main__':
    
    app.run(debug=True)
