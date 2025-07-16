import streamlit as st
import google.generativeai as genai
import os

# ==== CẤU HÌNH BAN ĐẦU ====

# --- Mật khẩu bảo vệ ứng dụng ---
PASSWORD = "ledacchien2024"  # Bạn có thể đổi mật khẩu này

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
    # Lấy API key từ Streamlit secrets
    google_api_key = st.secrets.get("GOOGLE_API_KEY")
    if not google_api_key:
        st.error("Lỗi: Vui lòng cung cấp GOOGLE_API_KEY trong tệp secrets.toml.")
        st.stop()
    genai.configure(api_key=google_api_key)
except Exception as e:
    st.error(f"Lỗi khi cấu hình Gemini: {e}")
    st.stop()

# ==== KIỂM TRA MẬT KHẨU ====
def check_password():
    """Hiển thị màn hình đăng nhập và kiểm tra mật khẩu."""
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    
    if not st.session_state["authenticated"]:
        st.title("🔒 Đăng nhập")
        st.write("Vui lòng nhập mật khẩu để truy cập ứng dụng.")
        password = st.text_input("Mật khẩu:", type="password")
        if st.button("Đăng nhập"):
            if password == PASSWORD:
                st.session_state["authenticated"] = True
                st.rerun() # Chạy lại app sau khi đăng nhập thành công
            else:
                st.error("Sai mật khẩu, vui lòng thử lại.")
        st.stop()

check_password()

# ==== KHỞI TẠO CHATBOT ====
def initialize_chat():
    """Khởi tạo mô hình và lịch sử chat nếu chưa có."""
    if "chat" not in st.session_state or "history" not in st.session_state:
        # Đọc các tệp cấu hình
        system_instruction = rfile("01.system_trainning.txt")
        model_name = rfile("module_gemini.txt").strip()
        initial_assistant_message = rfile("02.assistant.txt")

        if not all([system_instruction, model_name, initial_assistant_message]):
            st.error("Không thể khởi tạo chatbot do thiếu tệp cấu hình.")
            st.stop()

        # Khởi tạo mô hình GenerativeAI
        model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system_instruction
        )
        
        # Bắt đầu phiên chat với tin nhắn chào mừng của trợ lý
        st.session_state.chat = model.start_chat(history=[])
        st.session_state.history = [
            {"role": "model", "parts": [initial_assistant_message]}
        ]

initialize_chat()


# ==== GIAO DIỆN NGƯỜI DÙNG ====

# --- Hiển thị logo và tiêu đề ---
try:
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

# --- CSS để tùy chỉnh giao diện chat ---
st.markdown(
    """
    <style>
        .stChat .st-emotion-cache-1c7y2kd {
            flex-direction: column-reverse;
        }
        .stChatMessage[data-testid="stChatMessage"] {
            border-radius: 15px;
            padding: 12px;
            margin-bottom: 10px;
            max-width: 80%;
        }
        .stChatMessage[data-testid="stChatMessage"]:has-text("Bạn:") {
            background-color: #e1f5fe; /* Màu xanh nhạt cho người dùng */
            margin-left: auto;
        }
        .stChatMessage[data-testid="stChatMessage"]:has-text("Trợ lý:") {
            background-color: #f1f8e9; /* Màu xanh lá nhạt cho trợ lý */
            margin-right: auto;
        }
        .stChatMessage p {
            margin: 0;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Hiển thị lịch sử chat ---
for message in st.session_state.history:
    role = "Bạn" if message["role"] == "user" else "Trợ lý"
    with st.chat_message("assistant" if role == "Trợ lý" else "user"):
         st.markdown(f"**{role}:** {message['parts'][0]}")

# --- Ô nhập liệu và xử lý chat ---
if prompt := st.chat_input("Bạn cần tư vấn gì?"):
    # Hiển thị tin nhắn của người dùng ngay lập tức
    st.session_state.history.append({"role": "user", "parts": [prompt]})
    with st.chat_message("user"):
        st.markdown(f"**Bạn:** {prompt}")

    # Gửi tin nhắn đến Gemini và nhận phản hồi
    with st.chat_message("assistant"):
        with st.spinner("Trợ lý đang soạn câu trả lời..."):
            try:
                response = st.session_state.chat.send_message(prompt, stream=True)
                
                # Hiển thị phản hồi theo từng phần (streaming)
                def stream_handler():
                    for chunk in response:
                        yield chunk.text
                
                full_response = st.write_stream(stream_handler)

                # Lưu phản hồi hoàn chỉnh vào lịch sử
                st.session_state.history.append({"role": "model", "parts": [full_response]})

            except Exception as e:
                st.error(f"Đã xảy ra lỗi khi gọi API của Gemini: {e}")

