from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import os
from urllib.parse import urlparse

# Initialize app
app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

# ================= DATABASE CONFIG =================

db_url = os.environ.get("MYSQL_PUBLIC_URL")

if not db_url:
    raise Exception("MYSQL_PUBLIC_URL is not set in environment variables")

url = urlparse(db_url)

db_config = {
    'host': url.hostname,
    'user': url.username,
    'password': url.password,
    'database': url.path[1:],  # remove leading '/'
    'port': url.port,
    'connection_timeout': 5
}

# ================= ROUTES =================

@app.route('/')
def home():
    return app.send_static_file('index.html')

@app.route('/admin')
def admin():
    return app.send_static_file('admin.html')


# ================= REGISTER API =================

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    full_name = data.get('full_name')
    email = data.get('email')
    event_name = data.get('event_name')

    if not full_name or not email or not event_name:
        return jsonify({'message': 'All fields are required'}), 400

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Check duplicate registration
        cursor.execute(
            "SELECT * FROM registrations WHERE email = %s AND event_name = %s",
            (email, event_name)
        )

        if cursor.fetchone():
            return jsonify({'message': 'This email is already registered for this event!'}), 409

        # Insert data
        cursor.execute(
            "INSERT INTO registrations (full_name, email, event_name) VALUES (%s, %s, %s)",
            (full_name, email, event_name)
        )

        conn.commit()

        return jsonify({'message': 'Registration successful!'}), 200

    except Exception as e:
        return jsonify({'message': f'Database error: {str(e)}'}), 500

    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass


# ================= ADMIN API =================

@app.route('/api/registrations', methods=['GET'])
def get_registrations():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM registrations ORDER BY registered_at DESC")
        rows = cursor.fetchall()

        for row in rows:
            row['registered_at'] = row['registered_at'].strftime('%Y-%m-%d %H:%M:%S')

        return jsonify(rows), 200

    except Exception as e:
        return jsonify({'message': f'Database error: {str(e)}'}), 500

    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass


# ================= RUN APP =================

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)