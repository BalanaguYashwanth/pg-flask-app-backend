from flask import Flask,jsonify,request,send_file,Blueprint
from flask_restful import Resource,Api
import os

import pyrebase
import json
import firebase_admin
from firebase_admin import auth
from werkzeug.security import generate_password_hash
from firebase_admin import credentials, firestore, initialize_app
from flask_cors import CORS
import requests
#from exceptions import Exception
from PIL import Image
from io import BytesIO
from werkzeug.utils import secure_filename
import io
from google.cloud import storage

#from flask_wtf.csrf import CSRFProtect
#else

import datetime 
from google.api_core.datetime_helpers import DatetimeWithNanoseconds
from flask_wtf import csrf, Form
import os

app = Flask(__name__)
CORS(app)
cred = credentials.Certificate('key.json')
default_app = firebase_admin.initialize_app(cred)
db = firestore.client()
pb = pyrebase.initialize_app(json.load(open('fbconfig.json')))
todo_ref = db.collection('todos')
storage = pb.storage()

SECRET_KEY = os.urandom(32)
#print(SECRET_KEY)
app.config['SECRET_KEY'] = SECRET_KEY

#csrf = CSRFProtect(app)

# api_blueprint = Blueprint('api', __name__)
# #csrf.exempt(api_blueprint)
# app.register_blueprint(api_blueprint)

@app.route("/")
def hello():
    return "successfully done"
   
@app.route('/getcurrentuser',methods=['POST'])
def done():
    alldetails={}

    try:
        uid=request.json['uid']
        user = auth.get_user(uid)
        alldetails['uid']=user.uid
        alldetails['display_name']=user.display_name
        alldetails['email']=user.email
        alldetails['photo_url']=user.photo_url
        alldetails['emailverified']=user.email_verified
        alldetails['owner']=user.custom_claims.get('owner')
        if user.custom_claims.get('admin'):
            alldetails['admin']=user.custom_claims.get('admin')
        else:
            alldetails['admin']=False    
        return alldetails
    except:
        return jsonify({'message':False}),400


@app.route('/token',methods=['GET'])
def token():
    token=csrf.generate_csrf()
    return jsonify({'token':token}), 201


@app.route('/deleteaccount/<object>',methods=['POST'])
def delaccount(object):
    uid=request.json['uid']
    id=request.json['id']
    try:
        db.collection(object).document(id).delete()
        auth.delete_user(uid)
        print('deleted your account successfully ')
        return jsonify({'message':'deleted your account successfully'}),200
    except:
        return jsonify({'message':'error in  deleting your account so your profile should not be empty, please fillup your profile and then delete your account'}),400 



@app.route('/imagecompressor',methods=['GET','POST'])
def photo():
    img = Image.open(request.files['img'])
    try:  
        filename=secure_filename(request.files['img'].filename)
        print(filename)
        #img = img.resize((160,300),Image.ANTIALIAS)
        img.save(filename,optimize=True,quality=70)
        print(img)
        storage.child("images/"+filename).put(img)
        #link=storage.child("images/"+filename).get_url(None)
        #print(link)
        return jsonify({'message':link}),200
    except:
        return jsonify({'message':'error in uploading image'}),400


#data=request.files('img')
#img=data['img']

@app.route('/resetpassword',methods=['POST'])
def reset():
    email=request.json['email']
   
    try:
        #link=auth.generate_password_reset_link(email, action_code_settings)
        link=pb.auth().send_password_reset_email(email)
        print(link)
        #send_custom_email(email, link)
        return jsonify({'message':'successfully sent the email once check'})
    except:
        return jsonify({'message':'error in your email try with valid emailId'}),400


@app.route('/updateuser',methods=['POST'])
def users():
    uid=request.json['uid']
    user=auth.update_user(
        uid,
        photo_url=request.json['photourl'],
        display_name=request.json['displayname'],
    )
    return 'done'


@app.route('/deletephoto/<object>',methods=['POST'])
def deleteimage(object):
    uid=request.json['uid']
    print(uid)
    user=db.collection(object).document(request.json['id']).update({
        "profilepic":request.json['photourl']
        })
    return 'updated'



@app.route('/signup',methods=['POST'])
def signup():
    email=request.json['email']
    password=request.json['password']
    if email is None or password is None:
       return jsonify({'message':'username and password must not in blank'}),400
    try:
        user = auth.create_user(
               email=email,
               password=password
        )
        print('user',user.uid)
        auth.set_custom_user_claims(user.uid, {'owner': True})
        user = pb.auth().sign_in_with_email_and_password(email, password)
        pb.auth().send_email_verification(user['idToken'])
        return jsonify({'message': f'Successfully created user and send verification link please activate your account '}),200
    except:
        if email:
            emailexists=auth.get_user_by_email(email)
            if(emailexists.uid):
                return jsonify({'message': 'user is already exists '}),400
        else:
            return jsonify({'message': 'error creating in user'}),400


@app.route('/csignup',methods=['POST'])
def csignup():
    email=request.json['email']
    password=request.json['password']
    if email is None or password is None:
       return jsonify({'message':'username and password must not in blank'}),400
    try:
        user = auth.create_user(
               email=email,
               password=password
        )
        print('user',user.uid)
        auth.set_custom_user_claims(user.uid, {'owner': False})

        user1 = pb.auth().sign_in_with_email_and_password(email, password)
        pb.auth().send_email_verification(user1['idToken'])

        return jsonify({'message': f'Successfully created user and send verification link please activate your account '}),200
    except:
        if email:
            emailexists=auth.get_user_by_email(email)
            if(emailexists.uid):
                return jsonify({'message': 'user is already exists '}),400
        return jsonify({'message': 'Error creating user'}),400



@app.route('/asignup',methods=['POST'])
def asignup():
    email=request.json['email']
    password=request.json['password']
    if email is None or password is None:
       return jsonify({'message':'username and password must not in blank'}),400
    try:
        user = auth.create_user(
               email=email,
               password=password
        )
        print('user',user.uid)
        auth.set_custom_user_claims(user.uid, {'admin': True})

        user1 = pb.auth().sign_in_with_email_and_password(email, password)
        pb.auth().send_email_verification(user1['idToken'])

        return jsonify({'message': f'Successfully created user and send verification link please activate your account '}),200
    except:
        if email:
            emailexists=auth.get_user_by_email(email)
            if(emailexists.uid):
                return jsonify({'message': 'user is already exists '}),400
        return jsonify({'message': 'Error creating user'}),400


@app.route('/asignin',methods=['POST'])
def asignin():
    email=request.json['email']
    password=request.json['password']
    if email is None or password is None:
        return jsonify({'message':'username and password must not to be empty'})
    try:
        user = pb.auth().sign_in_with_email_and_password(email, password)
        arr=''
       
        for x in user:
            if x == 'localId':
                arr=(user[x])
                
        user1= auth.get_user(arr)
        user2=user1.custom_claims.get('admin')
        user3=user1.email_verified
        if user2:
            if user3:
                return user
            else:
                return jsonify({'message':'please verify your account with your mailId'}),400
        else:
            return jsonify({'message':'You are not admin to access it'}),400

    except:
        return jsonify({'message':'invalid crendentails please enter with valid credentials'}),400


@app.route('/signin',methods=['POST'])
def signin():
    email=request.json['email']
    password=request.json['password']
    if email is None or password is None:
        return jsonify({'message':'username and password must not to be empty'})
    try:
        user = pb.auth().sign_in_with_email_and_password(email, password)
        arr=''
       
        for x in user:
            if x == 'localId':
                arr=(user[x])
                
        user1= auth.get_user(arr)
        user2=user1.custom_claims.get('owner')
        user3=user1.email_verified
        print(user3)
        #print(user2)
        if user2:
            if user3:
                return user
            else:
                return jsonify({'message':'please verify your account with your mailId'}),400
        else:
            return jsonify({'message':'You are not owner to access it'}),400
    except:
        return jsonify({'message':'invalid crendentails please enter with valid credentials'}),400



@app.route('/csignin',methods=['POST'])
def csignin():
    email=request.json['email']
    password=request.json['password']
    if email is None or password is None:
        return jsonify({'message':'username and passowrd must not to be empty'}),400
    try:
        user = pb.auth().sign_in_with_email_and_password(email,password)
        carr=''
        
        for x in user:
            if x == 'localId':
                carr=(user[x])
                
        cuser1 = auth.get_user(carr)
        cuser2 = cuser1.custom_claims.get('owner')
        cuser3=cuser1.email_verified
       # print(cuser2)
        if not cuser2:
            if cuser3:
                return user
            else:
                return jsonify({'message':'please verify your account with your mailId'}),400
        else:
            return jsonify({'message':'You are not customer to access it'}),400
    except:
        return jsonify({'message':'invalid crendentails please enter with valid credentials'}),400


@app.route('/post/<object>', methods=['POST']) 
def create(object):
    """
        create() : Add document to Firestore collection with request body
        Ensure you pass a custom ID as part of json body in post request
        e.g. json={'id': '1', 'title': 'Write a blog post'}
    """
    
    try:

        #id = request.json['id']
        db.collection(object).add(request.json)
        return jsonify({"success": True}), 200
    except Exception as e:
        return f"An Error Occured: {e}"


@app.route('/get/<object>', methods=['GET'])
def read(object):
    """
        read() : Fetches documents from Firestore collection as JSON
        todo : Return document that matches query ID
        all_todos : Return all documents
    """
    try:
        todo1={}
        # Check if ID was passed to URL query
        #todo_id = request.args.get('id')    
        if todo_ref:
            todo = db.collection(object).stream()
            # query = todo.order_by(u'timestamp', direction=firestore.Query.DESCENDING)
            # todox=query.stream()

            for users in todo:
                todo1[users.id]=(users.to_dict())
            return jsonify(todo1), 200
        else:
            all_todos = [doc.to_dict() for doc in todo_ref.stream()]
            return jsonify(all_todos)
    except Exception as e:
        return f"An Error Occured: {e}"


@app.route('/get1/<object>', methods=['GET'])
def read1(object):
    """
        read() : Fetches documents from Firestore collection as JSON
        todo : Return document that matches query ID
        all_todos : Return all documents
    """
    try:
        todo1={}
        # Check if ID was passed to URL query
        #todo_id = request.args.get('id')    
        if todo_ref:
            todo = db.collection(object)
            todo = todo.order_by(time('timestamp'), direction=firestore.Query.DESCENDING)
            todox=todo.stream()
            
            for users in todox:
                #print( users.to_dict())
                todo1[users.id]=(users.to_dict())

            return jsonify(todo1), 200
        else:
            all_todos = [doc.to_dict() for doc in todo_ref.stream()]
            return jsonify(all_todos)
    except Exception as e:
        return f"An Error Occured: {e}"

def time(obj):
    return obj

@app.route('/update', methods=['POST', 'PUT'])
def update():
    """
        update() : Update document in Firestore collection with request body
        Ensure you pass a custom ID as part of json body in post request
        e.g. json={'id': '1', 'title': 'Write a blog post today'}
    """
    try:
        id = request.json['id']
        todo_ref.document(id).update(request.json)
        return jsonify({"success": True}), 200
    except Exception as e:
        return f"An Error Occured: {e}"

@app.route('/delete/<object>/<id>', methods=['GET', 'DELETE'])
def delete(object,id):
    """
        delete() : Delete a document from Firestore collection
    """
    try:
        # Check for ID in URL query
        #todo_id = request.args.get(id)
        db.collection(object).document(id).delete()
        return jsonify({"success": True}), 200
    except Exception as e:
        return f"An Error Occured: {e}"



if __name__=="__main__":
    app.run(host='0.0.0.0', port=5000,debug=True)

