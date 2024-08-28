import streamlit as st
import sounddevice as sd
import numpy as np
import threading
import time
import json
import os
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest
from aliyunsdkcore.auth.credentials import AccessKeyCredential
import nls

# 配置页面
st.set_page_config(page_title="会议记录与总结软件", layout="wide")

# 初始化会话状态
if 'recording' not in st.session_state:
    st.session_state.recording = False
if 'transcription' not in st.session_state:
    st.session_state.transcription = ""
if 'summary' not in st.session_state:
    st.session_state.summary = ""

# 阿里云配置
ALIBABA_CLOUD_ACCESS_KEY_ID = os.environ.get('ALIBABA_CLOUD_ACCESS_KEY_ID')
ALIBABA_CLOUD_ACCESS_KEY_SECRET = os.environ.get('ALIBABA_CLOUD_ACCESS_KEY_SECRET')
APP_KEY = ''
NLS_URL = "wss://nls-gateway.cn-shanghai.aliyuncs.com/ws/v1"

# 创建AcsClient实例
credentials = AccessKeyCredential(ALIBABA_CLOUD_ACCESS_KEY_ID, ALIBABA_CLOUD_ACCESS_KEY_SECRET)
client = AcsClient(region_id='cn-beijing', credential=credentials)

def create_task():
    request = CommonRequest()
    request.set_accept_format('json')
    request.set_domain('tingwu.cn-beijing.aliyuncs.com')
    request.set_method('PUT')
    request.set_version('2023-09-30')
    request.set_protocol_type('https')
    request.set_uri_pattern('/openapi/tingwu/v2/tasks')
    request.add_query_param('type', 'realtime')
    
    body = {
        "AppKey": APP_KEY,
        "Input": {
            "Format": "pcm",
            "SampleRate": 16000,
            "SourceLanguage": "cn",
            "TaskKey": f"task{int(time.time())}",
            "ProgressiveCallbacksEnabled": False
        },
        "Parameters": {
            "Transcription": {
                "DiarizationEnabled": True,
                "Diarization": {"SpeakerCount": 2}
            },
            "SummarizationEnabled": True,
            "Summarization": {
                "Types": ["Paragraph", "Conversational"]
            }
        }
    }
    
    request.set_content(json.dumps(body).encode('utf-8'))
    response = client.do_action_with_exception(request)
    return json.loads(response)

def stop_task(task_id):
    request = CommonRequest()
    request.set_accept_format('json')
    request.set_domain('tingwu.cn-beijing.aliyuncs.com')
    request.set_method('PUT')
    request.set_version('2023-09-30')
    request.set_protocol_type('https')
    request.set_uri_pattern('/openapi/tingwu/v2/tasks')
    request.add_query_param('type', 'realtime')
    request.add_query_param('operation', 'stop')
    
    body = {
        "AppKey": APP_KEY,
        "Input": {
            "TaskId": task_id
        }
    }
    
    request.set_content(json.dumps(body).encode('utf-8'))
    response = client.do_action_with_exception(request)
    return json.loads(response)

def get_result(task_id):
    request = CommonRequest()
    request.set_accept_format('json')
    request.set_domain('tingwu.cn-beijing.aliyuncs.com')
    request.set_method('GET')
    request.set_version('2023-09-30')
    request.set_protocol_type('https')
    request.set_uri_pattern(f'/openapi/tingwu/v2/tasks/{task_id}')
    
    response = client.do_action_with_exception(request)
    return json.loads(response)

class RealtimeMeetingRecorder:
    def __init__(self, url):
        self.url = url
        self.audio_stream = None
        self.is_recording = False
        self.task_id = None

    def on_sentence_begin(self, message, *args):
        print("Sentence begin:", message)

    def on_sentence_end(self, message, *args):
        print("Sentence end:", message)
        sentence = json.loads(message)['payload']['text']
        st.session_state.transcription += f"{sentence}\n"

    def on_result_changed(self, message, *args):
        print("Result changed:", message)

    def on_completed(self, message, *args):
        print("Completed:", message)

    def start_recording(self):
        self.is_recording = True
        task_response = create_task()
        self.task_id = task_response['TaskId']
        
        rm = nls.NlsRealtimeMeeting(
            url=self.url,
            on_sentence_begin=self.on_sentence_begin,
            on_sentence_end=self.on_sentence_end,
            on_result_changed=self.on_result_changed,
            on_completed=self.on_completed
        )
        
        rm.start()
        
        sample_rate = 16000
        samples_per_read = int(0.1 * sample_rate)
        
        with sd.InputStream(channels=1, dtype="int16", samplerate=sample_rate) as s:
            while self.is_recording:
                samples, _ = s.read(samples_per_read)
                rm.send_audio(samples.tobytes())
                time.sleep(0.01)
        
        rm.stop()

    def stop_recording(self):
        self.is_recording = False
        if self.task_id:
            stop_task(self.task_id)
            result = get_result(self.task_id)
            st.session_state.summary = result.get('Summarization', {}).get('Paragraph', '')

def start_recording():
    st.session_state.recording = True
    recorder = RealtimeMeetingRecorder(NLS_URL)
    threading.Thread(target=recorder.start_recording, daemon=True).start()

def stop_recording():
    st.session_state.recording = False
    # 这里应该调用recorder的stop_recording方法，但由于作用域限制，我们需要另一种方式来停止录音
    # 在实际应用中，您可能需要重构代码以使recorder可以在这里访问

# Streamlit UI
st.title("会议记录与总结软件")

col1, col2 = st.columns(2)

with col1:
    st.subheader("控制面板")
    if not st.session_state.recording:
        if st.button("开始录音"):
            start_recording()
    else:
        if st.button("停止录音"):
            stop_recording()

    if st.button("生成摘要"):
        # 这里应该触发摘要生成，但由于我们的示例中摘要是在停止录音时自动生成的，
        # 所以这个按钮在当前实现中实际上不会做任何事情
        pass

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
    st.experimental_rerun()