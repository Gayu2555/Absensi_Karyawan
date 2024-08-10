import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mysqldb import MySQL
from datetime import datetime
import MySQLdb.cursors

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Konfigurasi MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = '#USE YOUR DB USERNAME'
app.config['MYSQL_PASSWORD'] = '#USE YOUR DB PASSWORD'
app.config['MYSQL_DB'] = '#USE YOUR DB NAME'

mysql = MySQL(app)

# Script Backend Komponen Kesuluruhan
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # Logic untuk hapus karyawan
    if request.method == 'POST' and 'delete_karyawan' in request.form:
        unik_id = request.form.get('delete_karyawan')
        cursor.execute('DELETE FROM karyawan WHERE unik_id = %s', (unik_id,))
        mysql.connection.commit()
        flash(f'Karyawan dengan Unik ID {unik_id} telah dihapus.', 'success')
    
    cursor.execute('''
        SELECT 
            k.unik_id,
            k.nama,
            k.tanggal_lahir,
            k.pendidikan_terakhir,
            k.alamat,
            k.foto,
            COUNT(a.id) AS jumlah_absen,
            COUNT(a.id) * 180000 AS akumulasi_gaji
        FROM 
            karyawan k
        LEFT JOIN 
            absensi a ON k.unik_id = a.unik_id
        GROUP BY 
            k.unik_id, k.nama, k.tanggal_lahir, k.pendidikan_terakhir, k.alamat, k.foto
    ''')
    karyawan_list = cursor.fetchall()

    return render_template('admin.html', karyawan_list=karyawan_list)

@app.route('/add_karyawan', methods=['GET', 'POST'])
def add_karyawan():
    if request.method == 'POST':
        nama = request.form.get('nama')
        tanggal_lahir = request.form.get('tanggal_lahir')
        pendidikan_terakhir = request.form.get('pendidikan_terakhir')
        alamat = request.form.get('alamat')
        foto = request.files['foto']

        if not nama or not tanggal_lahir or not pendidikan_terakhir or not alamat or not foto:
            flash('Semua field harus diisi!', 'danger')
            return redirect(url_for('admin'))

        # Generate Unik ID
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT MAX(id) AS max_id FROM karyawan')
        max_id = cursor.fetchone()['max_id'] or 0
        unik_id = f"KRY-{max_id + 1:05d}"

        # Simpan foto
        foto_filename = unik_id + "_" + foto.filename
        foto_path = os.path.join('static', 'uploads', foto_filename)
        foto.save(foto_path)

        # Insert ke database
        cursor.execute('''
            INSERT INTO karyawan (unik_id, nama, tanggal_lahir, pendidikan_terakhir, alamat, foto)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (unik_id, nama, tanggal_lahir, pendidikan_terakhir, alamat, foto_filename))
        mysql.connection.commit()

        flash(f'Karyawan berhasil ditambahkan dengan Unik ID: {unik_id}', 'success')
        return redirect(url_for('admin'))

    return render_template('admin.html')


# Rute untuk halaman absensi
@app.route('/absen', methods=['GET', 'POST'])
def absen():
    if request.method == 'POST':
        unik_id = request.form.get('unik_id')
        nama = request.form.get('nama')

        if not unik_id or not nama:
            flash('Unik ID dan Nama harus diisi!', 'danger')
            return redirect(url_for('absen'))

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM karyawan WHERE unik_id = %s AND nama = %s', (unik_id, nama))
        karyawan = cursor.fetchone()

        if karyawan:
            tanggal_absen = datetime.now()  # Mengambil tanggal saat ini
            # Tambahkan catatan absensi ke tabel absensi
            cursor.execute('INSERT INTO absensi (unik_id, tanggal_absen) VALUES (%s, %s)', (unik_id, tanggal_absen))

            # Perbarui nilai akumulasi gaji di tabel karyawan
            cursor.execute('UPDATE karyawan SET akumulasi_gaji = akumulasi_gaji + 180000 WHERE unik_id = %s', (unik_id,))
            mysql.connection.commit()

            flash('Absensi berhasil! Gaji telah diakumulasi.', 'success')
        else:
            flash('Karyawan tidak ditemukan atau data tidak sesuai.', 'danger')

    return render_template('absen.html')







if __name__ == '__main__':
    app.run(debug=True)
