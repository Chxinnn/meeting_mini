# app.py
import threading
import streamlit as st

from recorder import RealtimeMeetingRecorder
from aliyun_client import AliyunClient
import config


def main():
    st.set_page_config(page_title="会议记录与总结软件", layout="wide")
    st.title("会议记录与总结软件")
    # 初始化会话状态
    if 'recorder' not in st.session_state:
        aliyun_client = AliyunClient(
            access_key_id=config.ALIBABA_CLOUD_ACCESS_KEY_ID,
            access_key_secret=config.ALIBABA_CLOUD_ACCESS_KEY_SECRET,
            app_key=config.APP_KEY
        )
        st.session_state.recorder = RealtimeMeetingRecorder(config.NLS_URL, aliyun_client)
    if 'transcription' not in st.session_state:
        st.session_state.transcription = ""
    if 'summary' not in st.session_state:
        st.session_state.summary = ""

    # 实现Streamlit界面和交互逻辑
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("控制面板")
        if st.button("开始录音"):
            threading.Thread(target=st.session_state.recorder.start_recording, daemon=True).start()
            # TODO
            st.session_state.transcription = ""
        if st.button("停止录音"):
            st.session_state.summary = st.session_state.recorder.stop_recording()

    with col2:
        st.subheader("实时转录")
        st.text_area("转录内容", value=st.session_state.transcription, height=300, key="transcription_area")

    st.subheader("会议摘要")
    st.text_area("摘要内容", value=st.session_state.summary, height=200, key="summary_area")

    # 会议文本管理功能（基础实现）
    st.subheader("会议记录管理")
    if st.button("保存会议记录"):
        # 这里应该实现保存功能，比如保存到文件或数据库
        st.success("会议记录已保存")

    if st.button("清除当前记录"):
        st.session_state.transcription = ""
        st.session_state.summary = ""
        # st.experimental_rerun()


if __name__ == "__main__":
    main()
