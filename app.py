from flask import Flask,request,render_template,redirect,session,flash,url_for
import mysql.connector
from datetime import date as dt_date
from datetime import datetime
import csv


db_config={
    'host':'localhost',
    'user':'root',
    'password':'suryadb575**',
    'database':'traindb'
}

app=Flask(__name__)
app.secret_key = 'your-secret-key'


#connect python with database
def get_db_connection():
    conn=mysql.connector.connect(**db_config)
    return conn

@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/home')
def home():
    uid=session['userid']
    name=session['name']
    return render_template('home.html',uid=uid,name=name)



@app.route('/register',methods=['GET','POST'])
def register():
    if request.method=='POST':
        username=request.form['username']
        email=request.form['email']
        password=request.form['password']
        country=request.form['country']
        conn=get_db_connection()
        cursor=conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email=%s',(email,))
        user=cursor.fetchone()

        if user:
            flash("User Already Exists",'error')
            return render_template('register.html')
        else:
            cursor.execute('INSERT INTO users (username,email,password,country) VALUES (%s,%s,%s,%s)',(username,email,password,country))
            conn.commit()
            cursor.close()
            conn.close()
            flash('Registered Successfully', 'success')
            return redirect(url_for('login',username=username))
            

    return render_template('register.html')



@app.route('/login',methods=['GET','POST'])
def login():
    username=request.args.get('username')
    if request.method=="POST":
        
        email=request.form['email']
        password=request.form['password']
        conn=get_db_connection()
        cursor=conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM users WHERE email=%s AND password=%s',(email,password))
        user=cursor.fetchone()
        if user:
            session['userid'] = user['uid']
            session['name']=user['username']
            flash("Login Successful",'success')
            conn.close()
            cursor.close()
            return redirect('/home')
        else:
            flash("Incorrect Username or Password",'error')
            return render_template('login.html')

    return render_template('login.html',username=username)

@app.route('/book',methods=['GET','POST'])
def book():
    trains=[]
    if request.method=="POST":
        source=request.form['source']
        destination=request.form['destination']
        date=request.form['date']
        conn=get_db_connection()
        cursor=conn.cursor(dictionary=True) #generally cursor() expects tuples .. that's why ..
        cursor.execute('SELECT * FROM trains WHERE source=%s AND destination=%s AND date=%s',(source,destination,date))
        trains=cursor.fetchall()
        if trains:
            return render_template('searchresult.html',trains=trains)
        else:
            flash('No Trains Available','error')
            return render_template('book.html')
            
    return render_template('book.html')


@app.route('/booknow/<int:tid>',methods=['GET','POST'])
def booknow(tid):
    name=session['name']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True,buffered=True)
    cursor.execute("SELECT * FROM trains where tid=%s",(tid,))
    train= cursor.fetchone()
    today=dt_date.today().isoformat()
    cursor.close()
    conn.close()

    if not train:
        return "Train not found", 404

    if request.method=='POST':
        cardname=request.form['cardname']
        cardnumber=request.form['cardnumber']
        expirydate=request.form['expirydate']
        date=request.form['date']
        uid=session['userid']
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True,buffered=True)
        if len(cardnumber)==8:
            cursor.execute(f"SELECT date FROM trains WHERE tid={tid}")
            row=cursor.fetchone()
            traveldate=row['date']
            cursor.execute('INSERT INTO bookings (uid,tid,cardname,cardnumber,expirydate,date,traveldate) VALUES (%s,%s,%s,%s,%s,%s,%s)',(uid,tid,cardname,cardnumber,expirydate,date,traveldate))
            conn.commit()
            conn.close()
            cursor.close()
            flash("Payment Successful",'success')
            return redirect('/home')
        else:
            flash("Card Number Must be 8 Digits!",'error')
            return redirect(f'/booknow/{tid}')

    return render_template('booknow.html',train=train,today=today,name=name)

@app.route('/myjourney/<int:uid>')
def myjourney(uid):
    conn=get_db_connection()
    cursor=conn.cursor(dictionary=True)
    query = """
        SELECT 
            b.bid,
            b.date AS booking_date,
            b.traveldate,
            t.trainname,
            t.source,
            t.destination,
            t.date ,
            t.departure,
            t.arrival,
            t.price,
            t.status
        FROM bookings b
        JOIN trains t ON b.tid = t.tid AND b.traveldate=t.date
        WHERE b.uid = %s
        ORDER BY t.date DESC
    """

    cursor.execute(query, (uid,))
    journeys = cursor.fetchall()
    today = dt_date.today()
    for j in journeys:
        train_date = j['date']
    
        
        if train_date < today:
            j['timeline'] = 'Finished'
        elif train_date == today:
            j['timeline'] = 'Today'
        else:
            j['timeline'] = 'Upcoming'
    cursor.close()
    conn.close()
    return render_template('myjourney.html',journeys=journeys)

@app.route('/explore')
def explore():
    return render_template('explore.html')
@app.route('/india')
def india():
    return render_template('india.html')

@app.route('/swiss')
def swiss():
    return render_template('swiss.html')

@app.route('/norway')
def norway():
    return render_template('norway.html')



@app.route('/paymentsummary')
def paymentsummary():
    return render_template('paymentsummary.html')

@app.route('/view')
def view():
    trains=[]

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM trains")
    trains = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('view.html', trains=trains)


@app.route('/searchresult')
def searchresult():
    return render_template('searchresult')

@app.route('/adminlogin',methods=['GET','POST'])
def adminlogin():
    if request.method=='POST':
        adminname=request.form['adminname']
        adminpassword=request.form['adminpassword']
        conn=get_db_connection()
        cursor=conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM admin WHERE adminname=%s AND adminpassword=%s',(adminname,adminpassword))
        adn=cursor.fetchone()
        if adn:
            session['adminname']=adn['adminname']
            conn.close()
            cursor.close()
            return redirect('/admindashboard')
        else:
            flash('Incorrect Username or Password')
            return render_template('adminlogin.html')

    return render_template('adminlogin.html')

@app.route('/admindashboard',methods=['GET'])
def admindashboard():
    conn=get_db_connection()
    cursor=conn.cursor()
    cursor.execute("SELECT * FROM trains")
    result=cursor.fetchall()
    return render_template('admindashboard.html',result=result)

@app.route('/addTrain',methods=['POST','GET'])
def addTrain():
    if request.method=='POST':
        conn=get_db_connection()
        cursor=conn.cursor(dictionary=True)
        tid=request.form['tid']
        trainname=request.form['trainname']
        source=request.form['source']
        destination=request.form['destination']
        date=request.form['date']
        departure=request.form['departure']
        arrival=request.form['arrival']
        price=request.form['price']
        status=request.form['status']
        cursor.execute('SELECT * FROM trains WHERE tid=%s AND date=%s',(tid,date))
        data=cursor.fetchone()
        if not data:
            cursor.execute("INSERT INTO trains (tid,trainname,source,destination,date,departure,arrival,price,status) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",(tid,trainname,source,destination,date,departure,arrival,price,status))
            conn.commit()
            cursor.close()
            conn.close()
            flash("Train Added Successfully",'success')
            return redirect('/admindashboard')
        else:
            flash("Train Can't be Added",'error')
            return redirect('/addTrain')

    return render_template('addTrain.html')


@app.route('/updateTrain')
def updateTrain():
    conn=get_db_connection()
    cursor=conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM trains")
    traindata=cursor.fetchall()
    return render_template('updateTrain.html',traindata=traindata)

@app.route('/updateForm/<int:tid>',methods=['POST','GET'])
def updateForm(tid):
    if request.method=='POST':
        tid=request.form['tid']
        trainname=request.form['trainname']
        source=request.form['source']
        destination=request.form['destination']
        date=request.form['date']
        departure=request.form['departure']
        arrival=request.form['arrival']
        price=request.form['price']
        status=request.form['status']
        conn=get_db_connection()
        cursor=conn.cursor(dictionary=True)
        cursor.execute(f"UPDATE trains SET tid=%s,trainname=%s,source=%s,destination=%s,date=%s,departure=%s,arrival=%s,price=%s,status=%s WHERE tid={tid}",(tid,trainname,source,destination,date,departure,arrival,price,status))
        conn.commit()
        flash("Updated Successfully",'success')
        cursor.close()
        conn.close()
        return redirect('/updateTrain')
        
    conn=get_db_connection()
    cursor=conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM trains WHERE tid=%s",(tid,))
    tdata=cursor.fetchone()
    return render_template('updateForm.html',tdata=tdata)

@app.route('/deleteTrain')
def deleteTrain():
    conn=get_db_connection()
    cursor=conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM trains")
    data=cursor.fetchall()
    return render_template('deleteTrain.html',data=data)

@app.route('/delete/<int:tid>/<date>')
def delete(tid,date):
    conn=get_db_connection()
    cursor=conn.cursor(dictionary=True)
    cursor.execute("DELETE FROM trains WHERE tid=%s AND date=%s",(tid,date))
    conn.commit()
    if cursor.rowcount>0:
        flash("Deleted Successfully",'success')
        return redirect('/deleteTrain')

    else:
        flash("Could not Delete!",'error')
    
    cursor.close()
    conn.close()
    return redirect('/deleteTrain')

@app.route('/viewTrains')
def viewTrains():
    trains=[]

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM trains")
    trains = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('viewTrains.html', trains=trains)

@app.route('/viewBooking/<int:tid>')
def viewBooking(tid):
    conn=get_db_connection()
    cursor=conn.cursor(dictionary=True)
    cursor.execute(f"SELECT * FROM bookings WHERE tid={tid}")
    bookingdata=cursor.fetchall()
    return render_template('viewBooking.html',bookingdata=bookingdata)

@app.route('/viewBookings')
def viewBookings():
    conn=get_db_connection()
    cursor=conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM bookings")
    bookingdata=cursor.fetchall()
    return render_template('viewBookings.html',bookingdata=bookingdata)


@app.route('/importcsv',methods=['POST','GET'])
def importcsv():
    if request.method=='POST':
        file=request.files['csvfile']
        if not file.filename.endswith('.csv'):
            flash("Please Upload a Valid CSV File",'error')
            return redirect('/addTrain')
        else:
            conn=get_db_connection()
            cursor=conn.cursor(dictionary=True)
            stream=file.stream.read().decode('UTF-8').splitlines()
            reader=csv.DictReader(stream)
            added=0
            skipped=0
            for i in reader:
                cursor.execute('SELECT * FROM trains WHERE tid=%s AND date=%s',(i['tid'],i['date']))
                data=cursor.fetchone()
                if data:
                    skipped+=1
                else:
                    cursor.execute("INSERT INTO trains (tid,trainname,source,destination,date,departure,arrival,price,status) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",(i['tid'],i['trainname'],i['source'],i['destination'],i['date'],i['departure'],i['arrival'],i['price'],i['status']))
                    added+=1

            conn.commit()
            cursor.close()
            conn.close()
            if added==0:
                flash("All Events Are Already Registered",'error')
                return redirect('/admindashboard')
            else:
                flash(f"{added} CSV Files Imported and Event Added Succesfully and {skipped} CSV Files are Already Registerd",'success')
                return redirect('/admindashboard')
                    
    return render_template('addTrain.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged Out Successfully",'error')
    return redirect('/')

@app.route('/adnlogout')
def adnlogout():
    session.clear()
    flash("Logged Out Successfully",'success')
    return redirect('/')



if __name__=='__main__':
    app.run(debug=True)