from flask import Flask, request, jsonify ,render_template
import firebase_admin
from firebase_admin import credentials, messaging, db
from flask_cors import CORS
from datetime import datetime

# Flask 앱 초기화
app = Flask(__name__)
CORS(app)

# Firebase 인증 및 초기화
cred = credentials.Certificate("expo-fcm-72d8f-firebase-adminsdk-helot-513471b905.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://routinebuildertest-default-rtdb.firebaseio.com/'
})

# Firebase Realtime Database 참조
users_ref = db.reference("users")

@app.route("/")
def home():
    return "FCM Notification Server is running!"

# 알림 전송 엔드포인트
@app.route("/sendNotification", methods=["POST"])
def send_notification():
    try:
        data = request.get_json()
        email = data.get("email")
        title = data.get("title", "운동 알림")
        body = data.get("body", "활동을 늘려보세요!")

        if not email:
            return jsonify({"error": "Email is required"}), 400

        # Find user by email
        print(f"Processing notification for email: {email}")
        user_data = find_user_by_email(email)
        print(f"Found user data: {user_data}")  # 사용자 데이터 확인
        if not user_data:
            return jsonify({"error": f"User not found for email: {email}"}), 404

        fcm_token = user_data.get("fcm_token")
        if not fcm_token:
            return jsonify({"error": f"FCM token not found for email: {email}"}), 404

        # Send FCM Notification
        send_fcm_notification(fcm_token, title, body)

        return jsonify({"success": f"Notification sent to {email}"}), 200

    except Exception as e:
        print(f"Error in send_notification: {e}")
        return jsonify({"error": str(e)}), 500


def process_single_email(email, title, body):
    """
    단일 이메일로 알림 전송 처리
    """
    user_data = find_user_by_email(email)
    if not user_data:
        return jsonify({"error": f"User not found for email: {email}"}), 404

    fcm_token = user_data.get("fcm_token")
    if not fcm_token:
        return jsonify({"error": f"FCM token not found for email: {email}"}), 404

    # FCM 알림 전송
    send_fcm_notification(fcm_token, title, body)

    return jsonify({"success": f"Notification sent to {email}"}), 200

def process_multiple_emails(emails, title, body):
    """
    다중 이메일로 알림 전송 처리
    """
    success_count = 0
    failure_count = 0

    for email in emails:
        user_data = find_user_by_email(email)
        if not user_data:
            print(f"User not found for email: {email}")
            failure_count += 1
            continue

        fcm_token = user_data.get("fcm_token")
        if not fcm_token:
            print(f"FCM token not found for email: {email}")
            failure_count += 1
            continue

        try:
            send_fcm_notification(fcm_token, title, body)
            success_count += 1
        except Exception as e:
            print(f"Error sending notification to {email}: {e}")
            failure_count += 1

    return jsonify({
        "success": f"Notifications sent to {success_count} users",
        "failure": f"Failed to send notifications to {failure_count} users"
    }), 200

def find_user_by_email(email):
    """
    이메일로 사용자 데이터 찾기
    """
    users = users_ref.get()
    for user_id, user_info in users.items():
        if user_info.get("email") == email:
            user_info["id"] = user_id  # 사용자 ID 추가
            return user_info
    return None

def send_fcm_notification(fcm_token, title, body):
    """
    FCM 알림 전송
    """
    print(f"Sending notification to token: {fcm_token}")
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            token=fcm_token
        )
        response = messaging.send(message)
        print(f"Notification sent successfully: {response}")
    except Exception as e:
        print(f"Error sending FCM notification: {e}")
        raise e

# Flask 서버 실행
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
