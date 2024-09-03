import os
import nls
import json
import time
import sounddevice as sd
import threading
import streamlit as st
import requests
import config
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest
from aliyunsdkcore.auth.credentials import AccessKeyCredential

class AliyunClient:
    def __init__(self, access_key_id, access_key_secret, app_key, region_id='cn-beijing'):
        self.app_key = app_key
        credentials = AccessKeyCredential(access_key_id, access_key_secret)
        self.client = AcsClient(region_id=region_id, credential=credentials)

    def build_request(self, summarization_enabled, task_id, status):
        global body
        request = CommonRequest()
        request.set_accept_format('json')
        request.set_domain('tingwu.cn-beijing.aliyuncs.com')
        request.set_method('PUT')
        request.set_version('2023-09-30')
        request.set_protocol_type('https')
        request.set_uri_pattern('/openapi/tingwu/v2/tasks')
        request.add_query_param('type', 'realtime')
        if status == 'get':
            request.set_method('GET')
            request.set_uri_pattern('/openapi/tingwu/v2/tasks' + '/' + task_id)
            return request
        if status == 'start':
            body = {
                "AppKey": self.app_key,
                "Input": {
                    "Format": "pcm",
                    "SampleRate": 16000,
                    "SourceLanguage": "cn",
                    "TaskKey": f"task{int(time.time())}",
                    "ProgressiveCallbacksEnabled": False
                },
                "Parameters": {
                    "Transcription": {
                        "OutputLevel": 1,
                        "DiarizationEnabled": True,
                        "Diarization": {"SpeakerCount": 2}
                    },
                    "AutoChaptersEnabled": True,
                    "SummarizationEnabled": summarization_enabled,
                    "Summarization": {
                        "Types": ["Paragraph", "Conversational"]
                    }
                }
            }
        if status == 'stop':
            body = {
                'AppKey': self.app_key,
                'Input': {
                    'TaskId': task_id
                }
            }
            request.add_query_param('operation', 'stop')
        request.set_content(json.dumps(body).encode('utf-8'))
        return request

    def create_task(self, summarization_enabled):
        request = self.build_request(summarization_enabled, '0', 'start')
        response = self.client.do_action_with_exception(request)
        response_json = json.loads(response)
        if response_json['Message'] == 'success':
            print("创建消息接收成功")
        task_id = response_json['Data']['TaskId']
        meeting_join_url = response_json['Data']['MeetingJoinUrl']
        return task_id, meeting_join_url

    def stop_task(self, task_id):
        request = self.build_request(False, task_id, 'stop')
        response = self.client.do_action_with_exception(request)
        response_json = json.loads(response)
        if response_json['Message'] == 'success':
            print("停止消息接收成功")
        task_status = response_json['Data']['TaskStatus']
        print(task_status)
        print(task_id)
        return task_status

    def get_result(self, task_id):
        request = self.build_request(False, task_id, 'get')
        response = self.client.do_action_with_exception(request)
        response_json = json.loads(response)
        print(json.dumps(response_json, indent=4, ensure_ascii=False))
        if response_json['Message'] == 'success':
            print("查询消息接收成功")
        result = response_json['Data'].get('Result', {})
        print(response_json)
        task_status = response_json['Data']['TaskStatus']
        if task_status == 'FAILED':
            print('FAILED' + response_json['Data']['ErrorCode'] + response_json['Data']['ErrorMessage'])
            return "FAILED", result
        if task_status == 'ONGOING' and not result:
            print("ONGOING BUT NOT RESULT")
            return "ONGOING BUT NOT RESULT", result
        if task_status == 'ONGOING' and result:
            print("ONGOING AND RESULT")
            return "ONGOING && SOME RESULT", result
        if task_status == 'COMPLETED':
            print("COMPLETED")
            return "COMPLETED", result
        return "OTHER", {"1": "2"}

class LocalAudioRecorder:
    def __init__(self, aliyun_client):
        self.aliyun_client = aliyun_client
        self.is_recording = False
        self.task_id = None
        self.meeting_join_url = None
        self.rm = None
        self.transcription = ""
        self.summary = ""
        self.recording_thread = None
        
    def start_recording(self):
        self.is_recording = True
        task_response = self.aliyun_client.create_task(summarization_enabled=True)
        self.task_id = task_response[0]
        self.meeting_join_url = task_response[1]
        
        print(f"TaskId: {self.task_id}")
        print(f"MeetingJoinUrl: {self.meeting_join_url}")
        
        # 初始化NlsRealtimeMeeting
        self.rm = nls.NlsRealtimeMeeting(
            url=self.meeting_join_url,
            on_sentence_begin=self.on_sentence_begin,
            on_sentence_end=self.on_sentence_end,
            on_result_changed=self.on_result_changed,
            on_completed=self.on_completed
        )
        self.rm.start()
        
        # 开始录音线程
        self.recording_thread = threading.Thread(target=self._record_audio)
        self.recording_thread.start()
    
    def _record_audio(self):

        sample_rate = 16000
        samples_per_read = int(0.1 * sample_rate)
        with sd.InputStream(channels=1, dtype="int16", samplerate=sample_rate) as stream:
            while self.is_recording:
                samples, overflowed = stream.read(samples_per_read)
                if overflowed:
                    print("Audio buffer has overflowed")
                self.rm.send_audio(samples.tobytes())
                time.sleep(0.01)

        
    def stop_recording(self):
        self.is_recording = False
        if self.recording_thread:
            self.recording_thread.join()  # 等待录音线程结束
            self.recording_thread = None
        if self.rm is not None:
            self.rm.stop()
            self.rm = None
        if self.task_id:
            self.aliyun_client.stop_task(self.task_id)

    def on_sentence_begin(self, message, *args):
        print("Sentence begin")

    def on_sentence_end(self, message, *args):
        print("Sentence end")
        sentence = json.loads(message)['payload']['result']
        print(sentence)
        self.transcription += f"{sentence}\n"

    def on_result_changed(self, message, *args):
        pass

    def on_completed(self, message, *args):
        pass

    def get_summary(self):
        if self.task_id:
            message, json_result = self.aliyun_client.get_result(self.task_id)
            print(message)
            print(json_result)
            return message, json_result
        else:
            return "NO_TASK_ID", {1: 2}

def req_head(json_result):
    autochapters_url = json_result.get('AutoChapters')
    if autochapters_url:
        response = requests.get(autochapters_url)
        if response.status_code == 200:
            autochapters_content = response.json()
            if 'AutoChapters' in autochapters_content:
                headline = dict(autochapters_content['AutoChapters'][0]).get("Headline")
                return headline
            else:
                file_name = f"{time.strftime('%Y_%m_%d_%H_%M_%S', time.localtime(time.time()))}"
                return file_name
        else:
            return f"Failed to retrieve data from {autochapters_url}, status code: {response.status_code}"
    else:
        return "autochapters URL not found in json_result"

def req_summary(json_result):
    summarization_url = json_result.get('Summarization')
    if summarization_url:
        response = requests.get(summarization_url)
        if response.status_code == 200:
            summarization_content = response.json()
            if not summarization_content['Summarization']:
                return "ConversationalSummary not found"
            speaker_summary = {
                item['SpeakerName']: item['Summary'] + '\n'
                for item in summarization_content['Summarization']['ConversationalSummary']
            }
        else:
            return f"Failed to retrieve data from {summarization_url}, status code: {response.status_code}"
    else:
        return "Summarization URL not found in json_result"
    formatted_speaker_summary = "".join(
        [f"{speaker}:\n\t{summary.strip()}\n" for speaker, summary in speaker_summary.items()])
    return formatted_speaker_summary

def main():
    aliyun_client = AliyunClient(
        access_key_id=config.ALIBABA_CLOUD_ACCESS_KEY_ID,
        access_key_secret=config.ALIBABA_CLOUD_ACCESS_KEY_SECRET,
        app_key=config.APP_KEY
    )
    
    st.set_page_config(page_title="会议记录与总结软件", layout="wide")
    st.title("会议记录与总结软件")
    
    if 'recorder' not in st.session_state:
        st.session_state.recorder = LocalAudioRecorder(aliyun_client)
    recorder = st.session_state.recorder
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("控制面板")
        if st.button("开始录音"):
            recorder.start_recording()
            st.success("录音已开始")
        
        if st.button("停止录音"):
            recorder.stop_recording()
            st.success("录音已停止")
        
    with col2:
        st.subheader("会议内容")
        st.text_area("转录内容", value=recorder.transcription, height=250, key="transcription_area")
        if st.button("显示摘要"):
            message, json_result = recorder.get_summary()
            if message == "COMPLETED":
                summary = req_summary(json_result)
                if summary == "ConversationalSummary not found":
                    st.session_state.summary = "会议录音内容不足！"
                else:
                    headline = req_head(json_result)
                    summary = req_summary(json_result)
                    st.session_state.title = headline
                    st.session_state.summary = f"标题：\n{headline}\n\n" \
                                               f"会议内容：\n{recorder.transcription}\n" \
                                               f"总结：\n{summary}\n"
            elif message in ["ONGOING BUT NOT RESULT", "ONGOING && SOME RESULT"]:
                st.session_state.summary = "摘要任务处理中..."
            elif message == "NO_TASK_ID":
                st.session_state.summary = "无会议记录！"

    st.subheader("会议摘要")
    st.text_area("摘要内容", value=st.session_state.summary if 'summary' in st.session_state else "", height=400, key="summary_area")

    # 会议文本管理功能
    save_path = "saved_meeting_records"
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    col3, col4 = st.columns(2)

    with col3:
        st.subheader("会议记录管理")
        meeting_title = st.session_state.title if 'title' in st.session_state else ""
        summary = st.session_state.summary if 'summary' in st.session_state else ""
        if st.button("保存会议记录"):
            if meeting_title and summary:
                file_path = os.path.join(save_path, f"{meeting_title}.txt")
                with open(file_path, "w") as f:
                    f.write(summary)
                st.success(f"会议记录已保存至'{meeting_title}.txt'中")
            elif not meeting_title:
                st.error("会议记录文件名生成失败!")
            elif not summary:
                st.error("未生成会议摘要!")

        if st.button("清除当前记录"):
            recorder.transcription = ""
            st.session_state.summary = ""
            st.session_state.title = ""
            recorder.task_id = None
            st.experimental_rerun()

    with col4:
        st.subheader("已保存的会议记录")
        saved_records = os.listdir(save_path)
        if saved_records:
            selected_record = st.selectbox("选择一个会议记录查看", saved_records)
            if selected_record:
                with open(os.path.join(save_path, selected_record), "r") as f:
                    st.text_area("会议记录", value=f.read(), height=400)
        else:
            st.info("当前没有已保存的会议记录")

if __name__ == "__main__":
    main()