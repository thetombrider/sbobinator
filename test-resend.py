import requests

def send_test_email():
    resend_api_key = "re_8sWyVNMd_QC6GNqdRfnpLmga66nUWykXy"
    url = "https://api.resend.com/emails"
    headers = {
        "Authorization": f"Bearer {resend_api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "from": "sbobinator@minutohomeserver.xyz",  # Use a verified 'from' address
        "to": ["tommasominuto@gmail.com"],
        "subject": "Test Email",
        "html": "<strong>Test email body</strong>"
    }
    response = requests.post(url, headers=headers, json=data)
    print("Status Code:", response.status_code)
    print("Response:", response.json())

send_test_email()