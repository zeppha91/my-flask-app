from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
from collections import Counter
from flask import Flask, render_template
import threading
import os

# Khởi tạo Flask app
app = Flask(__name__)

# Biến toàn cục để lưu trữ xác suất và số được thay thế
global_stats = {
    "tens": [],  # Danh sách (số, tần suất, xác suất) cho hàng chục
    "units": [],  # Danh sách (số, tần suất, xác suất) cho hàng đơn vị
    "suggested_tens": None,  # Số hàng chục được gợi ý (xác suất cao nhất)
    "suggested_units": None  # Số hàng đơn vị được gợi ý (xác suất cao nhất)
}

# Hàm chính để theo dõi dữ liệu và cập nhật xác suất
def monitor_game():
    global global_stats
    # Cấu hình ChromeDriver cho môi trường server
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Chạy ở chế độ không giao diện (headless)
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Đường dẫn đến file chromedriver (trên server sẽ được cài đặt tự động)
    chromedriver_path = "/usr/local/bin/chromedriver"  # Đường dẫn trên server (Render)

    try:
        service = Service(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("Đã khởi tạo trình duyệt Chrome thành công.")
    except Exception as e:
        print(f"Lỗi khởi tạo ChromeDriver: {e}")
        return

    # URL của trang web
    url = "https://42a.123s2hcy.com/home/mobile.html?gameId=110#/gamebet"

    try:
        # Mở trang web
        driver.get(url)
        print("Đang mở trang web. Chờ tải nội dung...")

        # Đợi trang tải
        time.sleep(10)

        # Lấy tiêu đề trang
        page_title = driver.title
        print(f"Tiêu đề trang: {page_title}")

        # Khởi tạo danh sách lưu kết quả
        tens_results = []  # Kết quả hàng chục (vị trí 5)
        units_results = []  # Kết quả hàng đơn vị (vị trí 6)
        check_count = 0  # Đếm số lần kiểm tra

        # Theo dõi giá trị --i trong các thẻ scroll-num
        print("\nBắt đầu theo dõi kết quả quay (vị trí 5 và 6) và cập nhật liên tục...")
        while True:
            try:
                # Tìm tất cả các thẻ <li> có class="scroll-num"
                scroll_nums = driver.find_elements(By.CSS_SELECTOR, "li.scroll-num")
                
                if len(scroll_nums) >= 6:  # Đảm bảo có đủ 6 phần tử
                    # Lấy giá trị --i từ vị trí 5 (hàng chục) và 6 (hàng đơn vị)
                    style_tens = scroll_nums[4].get_attribute("style")  # Vị trí 5 (index 4)
                    style_units = scroll_nums[5].get_attribute("style")  # Vị trí 6 (index 5)

                    tens_value = None
                    units_value = None

                    if style_tens and "--i" in style_tens:
                        start_idx = style_tens.index("--i:") + 4
                        end_idx = style_tens.index(";", start_idx)
                        tens_value = style_tens[start_idx:end_idx].strip()
                    if style_units and "--i" in style_units:
                        start_idx = style_units.index("--i:") + 4
                        end_idx = style_units.index(";", start_idx)
                        units_value = style_units[start_idx:end_idx].strip()

                    # Chuyển thành số nguyên và kiểm tra trong phạm vi 0-9
                    try:
                        if tens_value and 0 <= int(tens_value) <= 9:
                            tens_results.append(int(tens_value))
                            print(f"Kết quả hàng chục (vị trí 5): {tens_value}")
                        if units_value and 0 <= int(units_value) <= 9:
                            units_results.append(int(units_value))
                            print(f"Kết quả hàng đơn vị (vị trí 6): {units_value}")
                    except ValueError:
                        print(f"Giá trị không hợp lệ tại lần kiểm tra {check_count + 1}")

                # Tăng số lần kiểm tra
                check_count += 1
                print(f"Lần kiểm tra: {check_count}")

                # Cập nhật thống kê liên tục
                if tens_results or units_results:
                    # Thống kê hàng chục
                    if tens_results:
                        tens_counter = Counter(tens_results).most_common(5)
                        global_stats["tens"] = []
                        for num, freq in tens_counter:
                            probability = (freq / len(tens_results)) * 100
                            global_stats["tens"].append((num, freq, probability))
                        # Chọn số có xác suất cao nhất cho hàng chục
                        global_stats["suggested_tens"] = tens_counter[0][0]
                        print(f"Số gợi ý hàng chục (xác suất cao nhất): {global_stats['suggested_tens']}")
                    
                    # Thống kê hàng đơn vị
                    if units_results:
                        units_counter = Counter(units_results).most_common(5)
                        global_stats["units"] = []
                        for num, freq in units_counter:
                            probability = (freq / len(units_results)) * 100
                            global_stats["units"].append((num, freq, probability))
                        # Chọn số có xác suất cao nhất cho hàng đơn vị
                        global_stats["suggested_units"] = units_counter[0][0]
                        print(f"Số gợi ý hàng đơn vị (xác suất cao nhất): {global_stats['suggested_units']}")

                # Lưu kết quả vào file sau mỗi lần
                with open("game_results.txt", "a", encoding="utf-8") as file:
                    file.write(f"Thời gian: {time.ctime()} - Lần kiểm tra {check_count}\n")
                    if tens_value and 0 <= int(tens_value) <= 9:
                        file.write(f"Kết quả hàng chục: {tens_value}\n")
                    if units_value and 0 <= int(units_value) <= 9:
                        file.write(f"Kết quả hàng đơn vị: {units_value}\n")
                    if global_stats["suggested_tens"] is not None:
                        file.write(f"Số gợi ý hàng chục (xác suất cao nhất): {global_stats['suggested_tens']}\n")
                    if global_stats["suggested_units"] is not None:
                        file.write(f"Số gợi ý hàng đơn vị (xác suất cao nhất): {global_stats['suggested_units']}\n")
                    file.write("-" * 50 + "\n")

            except Exception as e:
                print(f"Lỗi trong vòng lặp: {e}")
                time.sleep(40)  # Tiếp tục chờ 40 giây ngay cả khi có lỗi

            # Đợi 40 giây trước khi kiểm tra lại
            time.sleep(40)

    except Exception as e:
        print(f"Có lỗi xảy ra: {e}")

    finally:
        driver.quit()

# Route cho trang web
@app.route('/')
def index():
    return render_template('index.html', stats=global_stats)

if __name__ == "__main__":
    # Kiểm tra nếu script không phải do Flask tự khởi động lại
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or os.environ.get("FLASK_ENV") != "development":
        monitor_thread = threading.Thread(target=monitor_game)
        monitor_thread.daemon = True
        monitor_thread.start()

    # Chạy Flask trong thread chính
    port = int(os.environ.get("PORT", 5000))  # Lấy port từ biến môi trường (Render yêu cầu)
    app.run(host='0.0.0.0', port=port)