from flask import Flask, jsonify, send_from_directory, render_template, request,Response,redirect,url_for,flash
import speech_recognition as sr
import cv2
import numpy as np
import face_recognition
import os
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from email.mime.text import MIMEText
from werkzeug.utils import secure_filename


app = Flask(__name__)
app.config['STATIC_FOLDER'] = 'static'
IMG_FOLDER = os.path.join('static', 'img', 'unknown')

app.config['UPLOAD_FOLDER'] = 'static/img/known'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.secret_key = "supersecretkey"

UPLOAD_FOLDER = os.path.join('static', 'img', 'known')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Email configuration
smtp_server = "smtp.gmail.com"
smtp_port = 587
smtp_user = "avijitdutta8798@gmail.com"
smtp_password = "jrgs yfmo slpc ifyb"
recipient_email = "avijitdutta7586@gmail.com"

# Directory configuration for face recognition
known_faces_dir = r"C:\Users\AVIJIT DUTTA\OneDrive\Desktop\raksha_alert\static\img\known"
unknown_faces_dir = r"C:\Users\AVIJIT DUTTA\OneDrive\Desktop\OJT_INTERNSHIP\static\img\unknown"

# Initialize face recognition
known_face_encodings = []
known_face_names = []
captured_unknown_face_encodings = []

# Load known faces
for image_name in os.listdir(known_faces_dir):
    image_path = os.path.join(known_faces_dir, image_name)
    image = face_recognition.load_image_file(image_path)
    face_encodings = face_recognition.face_encodings(image)
    
    if face_encodings:
        face_encoding = face_encodings[0]
        known_face_encodings.append(face_encoding)
        known_face_names.append(os.path.splitext(image_name)[0])

# Video stream URL
video_url = 'http://192.168.1.112:8080/video'
cap = cv2.VideoCapture(video_url)

# Sending email with the captured image
def send_email_with_image(unknown_image_path):
    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = recipient_email
    msg['Subject'] = 'Unknown Face Detected'

    body = 'An unknown face has been detected and saved as an image.'
    msg.attach(MIMEText(body, 'plain'))

    with open(unknown_image_path, 'rb') as attachment:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(unknown_image_path)}')
        msg.attach(part)

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        text = msg.as_string()
        server.sendmail(smtp_user, recipient_email, text)
        print(f"Email sent with image {unknown_image_path}")
    except Exception as e:
        print(f"Failed to send email: {e}")
    finally:
        server.quit()

# Generate video frames
def generate_frames():
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Convert the image from BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Find all the faces and face encodings in the current frame
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        for face_encoding, face_location in zip(face_encodings, face_locations):
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)

            if matches[best_match_index]:
                name = known_face_names[best_match_index]
            else:
                name = "Unknown"
                if not any(face_recognition.compare_faces(captured_unknown_face_encodings, face_encoding, tolerance=0.6)):
                    top, right, bottom, left = face_location
                    face_image = frame[top:bottom, left:right]
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    unknown_image_path = os.path.join(unknown_faces_dir, f"unknown_{timestamp}.jpg")
                    cv2.imwrite(unknown_image_path, face_image)

                    captured_unknown_face_encodings.append(face_encoding)

                    # Send email with the unknown face image
                    send_email_with_image(unknown_image_path)

            # Draw a box around the face
            top, right, bottom, left = face_location
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

            # Label the face with a name
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

        # Encode the frame as a JPEG and yield it as part of the video stream
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# Voice recognition and email sending
def send_email(recipient_email, subject, body):
    msg = MIMEText(body)
    msg['From'] = smtp_user
    msg['To'] = recipient_email
    msg['Subject'] = subject

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, recipient_email, msg.as_string())
        server.quit()
        return f"Email sent to {recipient_email} with subject '{subject}'"
    except Exception as e:
        return f"Failed to send email: {e}"

# Route to render the HTML page


# Route to handle voice recognition and email sending
@app.route('/send-email', methods=['POST'])
def send_email_route():
    try:
        data = request.get_json()
        command = data.get('command', '').lower()
        print(f"You said: {command}")

        if "police" in command:
            response = send_email("kmsuman27@gmail.com", "Alert: Police Assistance Needed", "This is an automated message requesting police assistance.")
        elif "padosi" in command:
            response = send_email("avijitdutta7586@gmail.com", "Alert: Neighbor Assistance Needed", "This is an automated message requesting neighbor assistance.")
        else:
            response = "No valid command recognized. Please say 'police' or 'padosi'."

        return jsonify({'message': response})

    except Exception as e:
        return jsonify({'error': f"Failed to process the request: {e}"})

# Route to serve live video feed
@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Route to serve live video page
@app.route('/')
def live_video():
    return render_template('video-page.html')

# Route to handle registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Process form data here
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        return 'Registration successful!'
    else:
        return render_template('register.html')

# Route to serve the login page
@app.route('/login')
def login():
    return render_template('login.html')
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/add_member', methods=['GET', 'POST'])
def add_member():
    uploaded_photo = None  # To pass the uploaded filename to the template
    
    # List all photos in the 'known' folder
    known_photos = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if allowed_file(f)]

    if request.method == 'POST':
        # Check if the form contains the 'photo' field
        if 'photo' not in request.files:
            flash('No file part')
            return redirect(request.url)

        file = request.files['photo']

        # Check if the user selected a file
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        # Check if the file is allowed and save it
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            uploaded_photo = filename
            flash('Member added successfully!')

            # After uploading a new photo, refresh the list of known photos
            known_photos = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if allowed_file(f)]

    return render_template('add_member.html', uploaded_photo=uploaded_photo, known_photos=known_photos)


# Route to handle account settings
@app.route('/account')
def account():
    return render_template('account.html')

@app.route('/unknown_person')
def unknown():
    return render_template('unknown.html')
@app.route('/images')
def list_images():
    # List all image files in the folder
    images = [img for img in os.listdir(IMG_FOLDER) if img.endswith(('jpg', 'jpeg', 'png', 'gif'))]
    return jsonify(images)

@app.route('/static/img/unknown/<filename>')
def get_image(filename):
    # Serve images from the folder
    return send_from_directory(IMG_FOLDER, filename)

@app.route('/delete_image/<filename>', methods=['DELETE'])
def delete_image(filename):
    try:
        file_path = os.path.join(IMG_FOLDER, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            return jsonify({'message': f'{filename} deleted successfully.'}), 200
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
