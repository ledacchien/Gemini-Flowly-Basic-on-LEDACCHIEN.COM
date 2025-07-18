import streamlit as st
import google.generativeai as genai
import os
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# ==== CẤU HÌNH BAN ĐẦU ====

# --- Cấu hình trang ---
# Phải là lệnh Streamlit đầu tiên, đặt layout thành "wide" để hiển thị đẹp hơn
st.set_page_config(page_title="Trợ lý AI", page_icon="🤖", layout="wide")

# --- Hàm đọc file ---
def rfile(name_file):
    """Hàm đọc nội dung từ file văn bản một cách an toàn."""
    try:
        with open(name_file, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        # Không hiển thị lỗi ở đây để tránh làm rối giao diện, hàm sẽ trả về None
        return None
    except Exception as e:
        st.error(f"Lỗi khi đọc tệp '{name_file}': {e}")
        return None

# --- Lấy API Key và cấu hình Gemini ---
try:
    google_api_key = st.secrets.get("GOOGLE_API_KEY")
    if not google_api_key:
        st.error("Lỗi: Vui lòng cung cấp GOOGLE_API_KEY trong tệp secrets.toml.")
        st.stop()
    genai.configure(api_key=google_api_key)
except Exception as e:
    st.error(f"Lỗi khi cấu hình Gemini: {e}")
    st.stop()

# --- GIAO DIỆN THANH BÊN (SIDEBAR) ---
with st.sidebar:
    st.title("⚙️ Tùy chọn")
    
    if st.button("🗑️ Xóa cuộc trò chuyện"):
        if "chat" in st.session_state: del st.session_state.chat
        if "history" in st.session_state: del st.session_state.history
        st.rerun()

    st.divider()
    st.markdown("Một sản phẩm của [Lê Đắc Chiến](https://ledacchien.com)")


# ==== KHỞI TẠO CHATBOT (PHIÊN BẢN CÓ TRÍ NHỚ - TÁCH FILE) ====
def initialize_chat():
    """Khởi tạo mô hình và lịch sử chat nếu chưa có."""
    if "chat" not in st.session_state or "history" not in st.session_state:
        model_name = rfile("module_gemini.txt")
        initial_assistant_message = rfile("02.assistant.txt")

        # --- ĐỌC DỮ LIỆU TỪ 2 FILE RIÊNG BIỆT ---
        role_instructions = rfile("01.system_trainning.txt")
        product_data = rfile("san_pham_va_dich_vu.txt")

        # Kiểm tra xem các file có được đọc thành công không
        if not all([model_name, role_instructions, product_data, initial_assistant_message]):
            st.error("Không thể khởi tạo chatbot do thiếu một trong các tệp cấu hình chính.")
            st.stop()

        # Ghép nội dung từ hai file lại với nhau để làm chỉ thị hệ thống
        system_instruction = f"{role_instructions}\n\n---\n\n{product_data}"
        # ----------------------------------------

        model = genai.GenerativeModel(
            model_name=model_name.strip(),
            system_instruction=system_instruction,
            safety_settings={
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
        )
        
        # Khởi tạo lại phiên trò chuyện có nhớ
        st.session_state.chat = model.start_chat(history=[])
        st.session_state.history = [
            {"role": "model", "parts": [initial_assistant_message]}
        ]

initialize_chat()

# ==== GIAO DIỆN NGƯỜI DÙNG ====

# --- Hiển thị logo và tiêu đề ---
# Kiểm tra sự tồn tại của file trước khi hiển thị để tránh crash app
logo_path = "system_data/logo.png"
if os.path.exists(logo_path):
    # Căn giữa logo với tỷ lệ [1, 1, 1] để logo to hơn
    logo_col1, logo_col2, logo_col3 = st.columns([1, 1, 1])
    with logo_col2:
        st.image(logo_path, use_container_width=True)

# Tương tự, kiểm tra sự tồn tại của file tiêu đề
title_path = "system_data/00.xinchao.txt"
if os.path.exists(title_path):
    title_content = rfile(title_path)
    if title_content:
        st.markdown(
            f"""<h1 style="text-align: center; font-size: 24px;">{title_content}</h1>""",
            unsafe_allow_html=True
        )

st.divider()

# --- Hiển thị lịch sử chat ---
for message in st.session_state.history:
    role = "assistant" if message["role"] == "model" else "user"
    with st.chat_message(role):
        st.markdown(message['parts'][0])

# --- Ô nhập liệu và xử lý chat ---
if prompt := st.chat_input("Bạn cần tư vấn gì?"):
    # Thêm tin nhắn của người dùng vào lịch sử và hiển thị ngay
    st.session_state.history.append({"role": "user", "parts": [prompt]})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Xử lý và hiển thị tin nhắn của AI
    with st.chat_message("assistant"):
        with st.spinner("Trợ lý đang soạn câu trả lời..."):
            try:
                # SỬ DỤNG send_message ĐỂ AI GHI NHỚ LỊCH SỬ
                response = st.session_state.chat.send_message(prompt, stream=True)
                
                def stream_handler():
                    for chunk in response:
                        yield chunk.text
                
                full_response = st.write_stream(stream_handler)
                # Thêm tin nhắn hoàn chỉnh của AI vào lịch sử để hiển thị
                st.session_state.history.append({"role": "model", "parts": [full_response]})

            except Exception as e:
                st.error(f"Đã xảy ra lỗi khi gọi API của Gemini: {e}")
