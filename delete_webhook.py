"""
Script để xóa webhook hiện tại của bot Telegram.
Sau khi chạy script này, bot sẽ có thể sử dụng polling mode.
"""

import urllib.request
import urllib.parse
import json
import os
import sys

# Lấy token từ environment variable hoặc sử dụng mặc định
TOKEN = os.getenv("BOT_TOKEN", "8643690918:AAF2cclKGfyECczdoQv1hvgAQ1Ym-nOicsE")

# Telegram API URL
API_URL = f"https://api.telegram.org/bot{TOKEN}"

def telegram_request(method, data=None):
    """Gửi request đến Telegram API"""
    url = f"{API_URL}/{method}"
    
    try:
        if data:
            data_bytes = json.dumps(data).encode('utf-8')
            req = urllib.request.Request(url, data=data_bytes, headers={'Content-Type': 'application/json'})
        else:
            req = urllib.request.Request(url)
        
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
            
    except Exception as e:
        print(f"❌ Lỗi kết nối: {e}")
        return None

def delete_webhook():
    """Xóa webhook hiện tại"""
    print("\n⏳ Đang xóa webhook...")
    result = telegram_request("deleteWebhook")
    
    if result:
        if result.get("ok"):
            print("✅ Webhook đã được xóa thành công!")
            print(f"   Kết quả: {result.get('result')}")
            return True
        else:
            print(f"❌ Lỗi: {result.get('description')}")
            return False
    return False

def get_webhook_info():
    """Lấy thông tin webhook hiện tại"""
    result = telegram_request("getWebhookInfo")
    
    if result and result.get("ok"):
        info = result.get("result", {})
        print("\n📋 Thông tin Webhook hiện tại:")
        print(f"   URL: {info.get('url', 'Chưa đặt')}")
        print(f"   Has custom certificate: {info.get('has_custom_certificate')}")
        print(f"   Pending updates: {info.get('pending_update_count')}")
        if info.get('last_error_date'):
            print(f"   Last error date: {info.get('last_error_date')}")
        if info.get('last_error_message'):
            print(f"   Last error message: {info.get('last_error_message')}")
        return info
    elif result:
        print(f"❌ Lỗi: {result.get('description')}")
    return None

if __name__ == "__main__":
    print("=" * 50)
    print("🗑️  XÓA WEBHOOK TELEGRAM BOT")
    print("=" * 50)
    
    # Kiểm tra webhook info trước
    get_webhook_info()
    
    # Xóa webhook
    success = delete_webhook()
    
    if success:
        # Kiểm tra lại
        print("\n📋 Kiểm tra lại sau khi xóa:")
        get_webhook_info()
        print("\n✅ Giờ bạn có thể chạy bot với polling mode!")
    else:
        print("\n❌ Không thể xóa webhook!")
        sys.exit(1)

