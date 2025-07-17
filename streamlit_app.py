import streamlit as st
import google.generativeai as genai
import os
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# ==== CẤU HÌNH BAN ĐẦU ====

# --- Hàm đọc file ---
def rfile(name_file):
    """Hàm đọc nội dung từ file văn bản một cách an toàn."""
    try:
        with open(name_file, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        st.error(f"Lỗi: Không tìm thấy tệp '{name_file}'. Vui lòng kiểm tra lại.")
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
        # Xóa model và history để khởi tạo lại hoàn toàn
        if "model" in st.session_state: del st.session_state.model
        if "history" in st.session_state: del st.session_state.history
        st.rerun()

    st.divider()
    st.markdown("Một sản phẩm của [Lê Đắc Chiến](https://ledacchien.com)")


# ==== KHỞI TẠO ỨNG DỤNG (PHIÊN BẢN KHÔNG TRÍ NHỚ - GỘP FILE) ====
def initialize_app():
    """Khởi tạo mô hình và lịch sử chat nếu chưa có."""
    if "model" not in st.session_state or "history" not in st.session_state:
        model_name = rfile("module_gemini.txt")
        initial_assistant_message = rfile("02.assistant.txt")

        # Đọc toàn bộ chỉ thị hệ thống từ một file duy nhất
        system_instruction = rfile("01.system_trainning.txt")

        # Kiểm tra xem các file có được đọc thành công không
        if not all([model_name, system_instruction, initial_assistant_message]):
            st.error("Không thể khởi tạo chatbot do thiếu một trong các tệp cấu hình.")
            st.stop()

        # Lưu model đã được cấu hình vào session_state
        st.session_state.model = genai.GenerativeModel(
            model_name=model_name.strip(),
            system_instruction=system_instruction,
            safety_settings={
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
        )
        
        # History vẫn cần để hiển thị giao diện chat
        st.session_state.history = [
            {"role": "model", "parts": [initial_assistant_message]}
        ]

initialize_app()

# ==== GIAO DIỆN NGƯỜI DÙNG ====
try:
    # Căn giữa logo
    col1, col2, col3 = st.columns([3, 2, 3])
    with col2:
        st.image("logo.png", use_container_width=True)
except FileNotFoundError:
    st.warning("Không tìm thấy tệp 'logo.png'.")

title_content = rfile("00.xinchao.txt")
if title_content:
    st.markdown(
        f"""<h1 style="text-align: center; font-size: 24px;">{title_content}</h1>""",
        unsafe_allow_html=True
    )

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
                # Sử dụng generate_content để AI không nhớ lịch sử
                response = st.session_state.model.generate_content(prompt, stream=True)
                
                def stream_handler():
                    for chunk in response:
                        yield chunk.text
                
                full_response = st.write_stream(stream_handler)
                # Thêm tin nhắn hoàn chỉnh của AI vào lịch sử để hiển thị
                st.session_state.history.append({"role": "model", "parts": [full_response]})

            except Exception as e:
                st.error(f"Đã xảy ra lỗi khi gọi API của Gemini: {e}")
