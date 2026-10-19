import streamlit as st
from datetime import datetime
import os
from openai import OpenAI
from storage import load_sessions, save_sessions, image_to_base64

# ============ 初始化状态 ============
if "sessions" not in st.session_state:
    saved = load_sessions()
    if saved:
        st.session_state.sessions = saved
        st.session_state.current_session = list(saved.keys())[0]
    else:
        default_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.session_state.sessions = {
            default_id: {
                "messages": [],
                "name": "小美",
                "personality": "温柔可爱一口台湾腔的台湾妹子"
            }
        }
        st.session_state.current_session = default_id

# ============ LLM 客户端 ============
client = OpenAI(
    api_key="sk-c9d62a5096fc435a909cf73741cff53d",
    base_url="https://api.deepseek.com/v1"
)

def stream_ai_response(session, user_input):
    """流式生成器：逐块 yield 模型输出"""
    system_prompt = (
        f"你的名字是{session['name']}，"
        f"你的性格是{session['personality']}。"
        f"请严格保持这个人设与用户对话，回复简短自然。"
    )
    messages = [{"role": "system", "content": system_prompt}]
    for msg in session["messages"][-10:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_input})

    stream = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        stream=True          # ★ 关键：开启流式
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta

# ============ 侧边栏 ============
with st.sidebar:
    st.header("AI控制面板")
    if st.button("📝 新建会话", use_container_width=True):
        new_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.session_state.sessions[new_id] = {
            "messages": [],
            "name": "小美",
            "personality": "温柔可爱一口台湾腔的台湾妹子"
        }
        st.session_state.current_session = new_id
        st.rerun()

    st.subheader("历史会话")
    for sid in list(st.session_state.sessions.keys()):
        col1, col2 = st.columns([4, 1])
        with col1:
            is_active = (sid == st.session_state.current_session)
            if st.button(
                f"📄 {sid}", key=f"select_{sid}", use_container_width=True,
                type="primary" if is_active else "secondary"
            ):
                st.session_state.current_session = sid
                st.rerun()
        with col2:
            if st.button("❌", key=f"del_{sid}"):
                del st.session_state.sessions[sid]
                if st.session_state.current_session == sid:
                    if st.session_state.sessions:
                        st.session_state.current_session = list(st.session_state.sessions.keys())[0]
                    else:
                        new_id = datetime.now().strftime("%Y%m%d_%H%M%S")
                        st.session_state.sessions[new_id] = {
                            "messages": [], "name": "小美",
                            "personality": "温柔可爱一口台湾腔的台湾妹子"
                        }
                        st.session_state.current_session = new_id
                st.rerun()

    st.divider()
    current = st.session_state.sessions[st.session_state.current_session]

    st.subheader("名字")
    new_name = st.text_input("名字", value=current["name"],
                                 label_visibility="collapsed", key="name_input")
    st.subheader("性格")
    new_personality = st.text_area("性格", value=current["personality"],
                                       label_visibility="collapsed", key="personality_input")
    current["name"] = new_name
    current["personality"] = new_personality
    



    st.divider()
    st.subheader("多模态输入")

    uploaded_image = st.file_uploader(
        "上传图片（jpg/png）",
        type=["jpg", "jpeg", "png"],
        key="image_uploader"
    )
    if uploaded_image:
        st.image(uploaded_image, caption="已上传图片", use_container_width=True)

    uploaded_audio = st.file_uploader(
        "上传语音（mp3/wav）",
        type=["mp3", "wav"],
        key="audio_uploader"
    )
    if uploaded_audio:
        st.audio(uploaded_audio, caption="已上传语音")

# ============ 主区域 ============
st.title("AI智能伴侣")
st.caption(f"当前会话: {st.session_state.current_session}")

for msg in current["messages"]:
    if msg["role"] == "user":
        with st.chat_message("user", avatar="🤖"):
            st.write(msg["content"])
    else:
        with st.chat_message("assistant", avatar="😊"):
            st.write(msg["content"])

if prompt := st.chat_input("请输入您的问题..."):
    # 若上传了图片，构造多模态消息内容
    if uploaded_image:
        img_b64 = image_to_base64(uploaded_image)
        content = [
            {"type": "text", "text": prompt},
            {"type": "image_url",
             "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
        ]
    else:
        content = prompt

    current["messages"].append({"role": "user", "content": content})

    with st.chat_message("user", avatar="🤖"):
        if uploaded_image:
            st.image(uploaded_image, width=200)
        st.write(prompt)

    # 流式回复
    with st.chat_message("assistant", avatar="😊"):
        response = st.write_stream(stream_ai_response(current, content))

    current["messages"].append({"role": "assistant", "content": response})
    save_sessions(st.session_state.sessions)