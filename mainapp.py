from flask import Flask, render_template, Response, request, jsonify
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

app = Flask(__name__)
app.config['STATIC_FOLDER'] = 'static'

# Email configuration
smtp_server = "smtp.gmail.com"
smtp_port = 587
smtp_user = "avijitdutta8798@gmail.com"
smtp_password = "jrgs yfmo slpc ifyb"
recipient_email = "avijitdutta7586@gmail.com"

# Directory configuration
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
video_url = 'http://192.168.137.127:8080/video'
cap = cv2.VideoCapture(video_url)

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

# Route to serve the homepage
@app.route('/')
def index():
    return render_template('index.html')

# Route to serve live video feed
@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Route to serve live video page
@app.route('/live_video')
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
        address1 = request.form['address1']
        address2 = request.form['address2']
        city = request.form['city']
        state = request.form['state']
        zip = request.form['zip']
        country = request.form['country']
        return 'Registration successful!'
    else:
        return render_template('register.html')

# Route to serve the login page
@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/account')
def account():
    return render_template('account.html')

@app.route('/categories')
def categories():
    return render_template('categories.html')

@app.route('/settings')
def settings():
    return render_template('settings.html')

@app.route('/forgot-password')
def forgotpassword():
    return render_template('forgot-password.html')

@app.route('/history')
def history():
    return render_template('history-page.html')

if __name__ == '__main__':
    app.run(debug=True)
