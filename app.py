import threading
import streamlit as st
from recorder import RealtimeMeetingRecorder
from aliyun_client import AliyunClient
import config
import time
import share_variable
def initialize_session_state():
    if 'is_recording' not in st.session_state:
        st.session_state.is_recording = False

def main():
    aliyun_client = AliyunClient(
            access_key_id=config.ALIBABA_CLOUD_ACCESS_KEY_ID,
            access_key_secret=config.ALIBABA_CLOUD_ACCESS_KEY_SECRET,
            app_key=config.APP_KEY
        )
    initialize_session_state() 
    st.set_page_config(page_title="会议记录与总结软件", layout="wide")
    st.title("会议记录与总结软件")

    recorder = RealtimeMeetingRecorder(config.NLS_URL, aliyun_client)
    
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("控制面板")
        if not st.session_state.is_recording:
            if st.button("开始录音"):
                st.session_state.is_recording = True
                threading.Thread(target=recorder.start_recording, daemon=True).start()
                #threading.Thread(target=update_transcription, daemon=True).start()
        else:
            if st.button("停止录音"):
                st.session_state.is_recording = False
                share_variable.stopflag = True
                recorder.stop_recording()
                # st.session_state.summary = st.session_state.recorder.stop_recording()
    with col2:
        st.subheader("实时转录")
        transcription_box = st.empty()  # 占位符

        try:
            while st.session_state.is_recording:
                # 只更新 text_area 的内容，不重新创建它
                transcription_box.write(recorder.transcription)
                time.sleep(1)  # 每秒刷新一次变量的值
        except KeyboardInterrupt:
            print("程序结束")

    

    # Meeting text management functionality
    st.subheader("会议记录管理")
    if st.button("保存会议记录"):
        # Implement saving functionality here
        st.success("会议记录已保存")

    if st.button("清除当前记录"):
        st.session_state.transcription = ""
        st.session_state.summary = ""

if __name__ == "__main__":
    main()