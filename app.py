# app.py
import streamlit as st

from recorder import RealtimeMeetingRecorder
from aliyun_client import AliyunClient
import config

def main():
    st.set_page_config(page_title="会议记录与总结软件", layout="wide")

    # 初始化会话状态
    if 'recorder' not in st.session_state:
        aliyun_client = AliyunClient(
            access_key_id=config.ALIBABA_CLOUD_ACCESS_KEY_ID,
            access_key_secret=config.ALIBABA_CLOUD_ACCESS_KEY_SECRET,
            app_key=config.APP_KEY
        )
        st.session_state.recorder = RealtimeMeetingRecorder(config.NLS_URL, aliyun_client)

    # 实现Streamlit界面和交互逻辑
    if st.button("开始录音"):
        st.session_state.recorder.start_recording()

    if st.button("停止录音"):
        summary = st.session_state.recorder.stop_recording()
        st.write("会议总结:", summary)


if __name__ == "__main__":
    main()
