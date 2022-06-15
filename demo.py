from flask import Flask,render_template,request,redirect,url_for
import mysql.connector
import hashlib
import pyqrcode
import png
from pyqrcode import QRCode
from PIL import Image
import os
from email.mime.multipart import MIMEMultipart
import smtplib

UPLOAD_FOLDER = 'static/img/'
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

mydb = mysql.connector.connect(host="127.0.0.1",user="root",password="",database="product")
mycursor = mydb.cursor()
@app.route('/')
@app.route('/login')
def index():
    return render_template('login.html')

@app.route('/add')
def admin():
    return render_template('admin.html')

@app.route('/view_prod')
def product():
    sql = "SELECT * FROM hash"
    mycursor.execute(sql)
    result = mycursor.fetchall()
    return render_template('product.html',data = result)

@app.route('/view_user')
def user():
    select_employee = "SELECT * FROM users"
    mycursor.execute(select_employee)
    result = mycursor.fetchall()
    return render_template('user.html',data = result)

@app.route('/validate',methods=['POST','GET'])
def block():
    global data1,data2
    if request.method == 'POST':
        data1 = request.form.get('username')
        data2 = request.form.get('password')
        sql = "SELECT * FROM `users` WHERE `name` = %s AND `password` = %s"
        val = (data1, data2)
        mycursor.execute(sql,val)
        account = mycursor.fetchone()
        print(account)
        if account:
            return redirect(url_for('dashboard'))
        elif data1 == 'admin' and data2 == '1234':
            return render_template('admin.html')
        else:
            return render_template('login.html',msg = 'Invalid')

@app.route('/dashboard')
def dashboard():
    sql = 'SELECT * FROM hash'
    mycursor.execute(sql)
    result = mycursor.fetchall()
    return render_template('dashboard.html',data = result)

@app.route('/mail',methods=['POST','GET'])
def mail():
    if request.method == 'POST':
        user = data1
        pw = data2
        prod_name = request.form.get('prod_name')
        prod_id = request.form.get('prod_id')
        price = request.form.get('price')
        sql = "SELECT * FROM `users` WHERE `name` = %s AND `password` = %s"
        val = (user,pw)
        mycursor.execute(sql,val)
        account = mycursor.fetchall()
        if account:
            for row1 in account:
                sql1 = "SELECT * FROM `hash` WHERE `prod_name` = %s AND `Prod_id` = %s"
                val1 = (prod_name,prod_id)
                mycursor.execute(sql1,val1)
                account1 = mycursor.fetchall()
                if account1:
                    for row in account1:
                        if row[6] == 'Original':
                            subject = 'Congrats! You have Selected Original Product'
                        elif row[6] == 'Duplicate':
                            subject = 'Oops! You have Selected Duplicate Product'
                    fromaddr = "smsk5308@gmail.com"
                    toaddr = row1[2]      
                    msg = MIMEMultipart() 
                    msg['From'] = fromaddr 
                    msg['To'] = toaddr 
                    msg['Subject'] = subject
                    s = smtplib.SMTP('smtp.gmail.com', 587) 
                    s.starttls() 
                    s.login(fromaddr, "jykpldsdllohokad") 
                    text = msg.as_string() 
                    s.sendmail(fromaddr, toaddr, text) 
                    s.quit()
                    sql = 'INSERT INTO cart (`name`, `prod_name`, `prod_id`, `price`) VALUES (%s, %s, %s, %s)'
                    val = (data1, prod_name, prod_id, price)
                    mycursor.execute(sql, val)
                    mydb.commit()
            return render_template('desc.html',data = account1)

@app.route('/register')
def reg():
    return render_template('register.html')

@app.route('/desc',methods=['POST','GET'])
def desc():
    global account1
    if request.method == 'POST':
        prod_name = request.form.get('prod_name')
        sql = "SELECT * FROM `hash` WHERE `prod_name` = %s"
        val = (prod_name, )
        mycursor.execute(sql, val)
        account1 = mycursor.fetchall()
        return render_template('desc.html',data = account1)

@app.route('/registerform',methods=['POST','GET'])
def register():
    if request.method == 'POST':
        user = request.form.get('name')
        mail = request.form.get('mail')
        phone = request.form.get('phone')
        password = request.form.get('password')
        sql = "INSERT INTO users (`name`, `email`, `phone`, `password`) VALUES (%s, %s, %s, %s)"
        val = (user, mail, phone, password)
        mycursor.execute(sql, val)
        mydb.commit()
        return render_template('dashboard.html')

@app.route('/upload',methods=['POST','GET'])
def upload():
    if request.method == 'POST':
        prod_name = request.form.get('prod_name')
        prod_id = request.form.get('prod_id')
        prod_type = request.form.get('prod_type')
        price = request.form.get('price')
        desc = request.form.get('desc')
        file1 = request.files['filename']
        prod_img = os.path.join(app.config['UPLOAD_FOLDER'], file1.filename)
        file1.save(prod_img)
        hashid = hashlib.sha256(prod_id.encode()).hexdigest()
        url = pyqrcode.create(prod_id)
        url.png('static/img/'+ prod_name + '.png', scale = 6)
        qr_img = 'static/img/'+ prod_name + '.png'
        if prod_type == "Duplicate":
            sql = 'SELECT * FROM `hash` WHERE `prod_id` = %s'
            val = (prod_id,)
            mycursor.execute(sql, val)
            result = mycursor.fetchall()
            if result:
                sql = 'SELECT * FROM `hash` WHERE `prod_id` = %s AND `prod_type` = %s'
                val = (prod_id, prod_type)
                mycursor.execute(sql, val)
                result = mycursor.fetchall()
                if result:
                    sql = "INSERT INTO hash (`prod_name`, `prod_id`, `prod_img`, `qr_code`, `hash_id`, `prod_type`, `price`, `desc`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
                    val = (prod_name, prod_id, prod_img, qr_img, hashid, prod_type, price, desc)
                    mycursor.execute(sql, val)
                    mydb.commit()
                else:
                    return render_template('error_prd.html',msg='Invalid Product')
            else:
                sql = "INSERT INTO hash (`prod_name`, `prod_id`, `prod_img`, `qr_code`, `hash_id`, `prod_type`, `price`, `desc`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
                val = (prod_name, prod_id, prod_img, qr_img, hashid, prod_type, price, desc)
                mycursor.execute(sql, val)
                mydb.commit()
        else:
            sql = "INSERT INTO hash (`prod_name`, `prod_id`, `prod_img`, `qr_code`, `hash_id`, `prod_type`, `price`, `desc`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
            val = (prod_name, prod_id, prod_img, qr_img, hashid, prod_type, price, desc)
            mycursor.execute(sql, val)
            mydb.commit()
        """sql = 'SELECT * FROM `hash` WHERE `prod_id` = %s AND `prod_type` = %s'
        val = (prod_id, 'Original')
        sql = "INSERT INTO hash (`prod_name`, `prod_id`, `prod_img`, `qr_code`, `hash_id`, `prod_type`, `price`, `desc`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        val = (prod_name, prod_id, prod_img, qr_img, hashid, prod_type, price, desc)
        mycursor.execute(sql, val)
        mydb.commit()"""
        return render_template('admin.html',msg='Product Added')

@app.route('/delete', methods = ['POST','GET'])
def delete():
    if request.method == 'POST':
        prod_name = request.form.get('prod_name')
        prod_id = request.form.get('prod_id')
        sql = 'DELETE FROM `hash` WHERE  `prod_name` = %s AND `prod_id` = %s'
        val = (prod_name, prod_id)
        mycursor.execute(sql,val)
        mydb.commit()
        return render_template('dashboard.html')

@app.route('/cart')
def cart():
    sql = 'SELECT * FROM `cart` WHERE `name` = %s'
    val = (data1,)
    mycursor.execute(sql, val)
    result = mycursor.fetchall()
    if result:
        return render_template('cart.html', data = result)
    return render_template('cart.html', msg = 'No Cart')

@app.route('/delete_cart', methods = ['POST','GET'])
def delete1():
    if request.method == 'POST':
        prod_name = request.form.get('prod_name')
        prod_id = request.form.get('prod_id')
        sql = 'DELETE FROM `cart` WHERE  `prod_name` = %s AND `prod_id` = %s'
        val = (prod_name, prod_id)
        mycursor.execute(sql,val)
        mydb.commit()
        return redirect(url_for('cart'))

@app.route('/search', methods = ['POST','GET'])
def search():
    if request.method == 'POST':
        prod_id = request.form.get('prod_id')
        sql = 'SELECT * FROM `hash` WHERE `prod_id` = %s'
        val = (prod_id, )
        mycursor.execute(sql, val)
        result = mycursor.fetchall()
        if result:
            return render_template('desc.html', data = result, ty = 'style=display:block')
        else:
            return render_template('Invalid Product ID')

if __name__ == '__main__':
    app.run(debug=True)
