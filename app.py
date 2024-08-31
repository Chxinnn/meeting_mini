# app.py
import nls
import json
import time
import queue
import pydub
import config
import streamlit as st
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest
from aliyunsdkcore.auth.credentials import AccessKeyCredential
from streamlit_webrtc import WebRtcMode, webrtc_streamer


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
                        "OutputLevel": 2,
                        "DiarizationEnabled": True,
                        "Diarization": {"SpeakerCount": 2}
                    },
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
        return task_status

    def get_result(self, task_id):
        request = self.build_request(False, task_id, 'get')
        response = self.client.do_action_with_exception(request)
        response_json = json.loads(response)
        print(json.dumps(response_json, indent=4, ensure_ascii=False))
        # TODO 当task_status == 'ONGOING'时response_json的Data中并没有result
        if response_json['Message'] == 'success':
            print("查询消息接收成功")
        task_status = response_json['Data']['TaskStatus']
        if task_status == 'FAILED':
            print('FAILED' + response_json['Data']['ErrorCode'] + response_json['Data']['ErrorMessage'])
        # if task_status == 'ONGOING' and not response_json['Data']['Result']:
        #     print("ONGOING BUT NOT RESULT")
        #     return None
        # if task_status == 'ONGOING' and response_json['Data']['Result']:
        #     print("ONGOING AND RESULT")
        #     return response_json['Data']['Result']
        if task_status == 'COMPLETED':
            print("COMPLETED")
            return response_json['Data']['Result']
        return "get_result_return"


class RealtimeMeetingRecorder:
    def __init__(self, url, aliyun_client):
        self.url = url
        self.aliyun_client = aliyun_client
        self.is_recording = False
        self.task_id = None
        self.meeting_join_url = None
        self.rm = None
        self.transcription = ""
        # self.transcription_callback = None
        self.summary = ""

    # def set_transcription_callback(self, callback):
    #     self.transcription_callback = callback

    # 实现各种回调方法和录音逻辑
    def on_sentence_begin(self, message, *args):
        # print("Sentence begin:", json.dumps(json.loads(message), indent=4, ensure_ascii=False))
        print("Sentence begin")

    def on_sentence_end(self, message, *args):
        # print("Sentence end:", json.dumps(json.loads(message), indent=4, ensure_ascii=False))
        print("Sentence end")
        sentence = json.loads(message)['payload']['result']
        print(sentence)
        self.transcription += f"{sentence}\n"
        # if self.transcription_callback:
        #     self.transcription_callback(self.transcription)

    def on_result_changed(self, message, *args):
        # print("Result changed:", json.dumps(json.loads(message), indent=4, ensure_ascii=False))
        # print("Result changed")
        pass

    def on_completed(self, message, *args):
        # print("Completed:", json.dumps(json.loads(message), indent=4, ensure_ascii=False))
        pass

    def start_recording(self):
        self.is_recording = True
        task_response = self.aliyun_client.create_task(summarization_enabled=True)
        print("start_recording")
        print("task创建完成")
        self.task_id = task_response[0]
        self.meeting_join_url = task_response[1]

        # print(f"TaskId: {self.task_id}")
        # print(f"MeetingJoinUrl: {self.meeting_join_url}")

        # 初始化会议实例
        self.rm = nls.NlsRealtimeMeeting(
            url=self.meeting_join_url,
            on_sentence_begin=self.on_sentence_begin,
            on_sentence_end=self.on_sentence_end,
            on_result_changed=self.on_result_changed,
            on_completed=self.on_completed
        )
        self.rm.start()

    def stop_recording(self):
        self.is_recording = False
        if self.rm is not None:
            self.rm.stop()
            self.rm = None
        if self.task_id:
            self.aliyun_client.stop_task(self.task_id)
            self.summary = self.aliyun_client.get_result(self.task_id)
            # return result.get('Summarization', {}).get('Paragraph', '')

    def send_audio(self, audio_data):
        if self.rm and self.is_recording:
            self.rm.send_audio(audio_data)


def app(status_indicator, webrtc_ctx, recorder):
    realtime_output = st.empty()
    try:
        # 主循环
        while recorder.is_recording:
            if webrtc_ctx.audio_receiver:
                # 创建一个空的 AudioSegment 对象用于存储接收到的音频数据
                sound_chunk = pydub.AudioSegment.empty()

                # 尝试从音频接收器获取音频帧
                try:
                    audio_frames = webrtc_ctx.audio_receiver.get_frames(timeout=1)
                except queue.Empty:
                    # 如果没有数据可用，等待一段时间并继续循环
                    time.sleep(0.1)
                    status_indicator.write("无音频帧输入！.")
                    continue

                status_indicator.write("启动成功！正在录音...")

                # 对每个音频帧进行处理
                for audio_frame in audio_frames:
                    # 将音频帧转换为 pydub 的 AudioSegment 对象
                    sound = pydub.AudioSegment(
                        data=audio_frame.to_ndarray().tobytes(),
                        sample_width=audio_frame.format.bytes,
                        frame_rate=audio_frame.sample_rate,
                        channels=len(audio_frame.layout.channels),
                    )
                    # 将当前音频片段添加到 sound_chunk
                    sound_chunk += sound

                if len(sound_chunk) > 0:
                    # 将音频调整为单声道并设置为 16kHz 采样率
                    sound_chunk = sound_chunk.set_channels(1).set_frame_rate(16000)
                    # 将音频数据转换为字节流并传递给 NlsRealtimeMeeting 实例
                    audio_data = sound_chunk.raw_data
                    recorder.rm.send_audio(audio_data)
                    # print(recorder.transcription)
                    st.session_state.transcription = recorder.transcription
                    realtime_output.markdown(f"**实时转录:** {recorder.transcription}")
            else:
                # 如果没有音频接收器，则结束循环
                status_indicator.write("AudioReceiver is not set. Abort.")
                break
    finally:
        recorder.stop_recording()


def main():
    st.set_page_config(page_title="会议记录与总结软件", layout="wide")
    st.title("会议记录与总结软件")
    if 'transcription' not in st.session_state:
        st.session_state.transcription = ""
    if 'summary' not in st.session_state:
        st.session_state.summary = ""

    aliyun_client = AliyunClient(
        access_key_id=config.ALIBABA_CLOUD_ACCESS_KEY_ID,
        access_key_secret=config.ALIBABA_CLOUD_ACCESS_KEY_SECRET,
        app_key=config.APP_KEY
    )
    # 初始化 RealtimeMeetingRecorder 实例
    recorder = RealtimeMeetingRecorder(config.NLS_URL, aliyun_client)
    # 设置 WebRTC 配置
    rtc_configuration = {
        'iceServers': [
            {'urls': 'stun:stun.l.google.com:19302'},
            {'urls': 'stun:stunserver.org'},
            {'urls': 'stun:stun01.sipphone.com'},
            {'urls': 'stun:stun.ekiga.net'},
            {'urls': 'stun:stun.ideasip.com'},
            {'urls': 'stun:stun.xten.com'}
        ]
    }

    # 实现Streamlit界面和交互逻辑
    col1, col2 = st.columns(2)

    with col2:
        st.subheader("会议内容")
        st.text_area("转录内容", value=st.session_state.transcription, height=250, key="transcription_area")
        col2_col1, col2_col2 = st.columns(2)
        with col2_col1:
            if st.button("生成摘要"):
                # TODO 生成摘要
                st.session_state.summary = recorder.summary
                pass
        with col2_col2:
            if st.button("获取音频"):
                # TODO 获取会议音频
                pass

    with col1:
        st.subheader("控制面板")
        webrtc_ctx = webrtc_streamer(
            key="speech-to-text",
            mode=WebRtcMode.SENDONLY,
            audio_receiver_size=20480,
            rtc_configuration=rtc_configuration,
            media_stream_constraints={"video": False, "audio": True},
        )

        status_indicator = st.empty()

        if webrtc_ctx.state.playing:
            status_indicator.write("正在启动会议...")
            recorder.start_recording()
            app(status_indicator, webrtc_ctx, recorder)

    st.subheader("会议摘要")
    st.text_area("摘要内容", value=st.session_state.summary, height=200, key="summary_area")

    # TODO 会议文本管理功能
    st.subheader("会议记录管理")
    if st.button("保存会议记录"):
        # 这里应该实现保存功能，比如保存到文件或数据库
        st.success("会议记录已保存")

    if st.button("清除当前记录"):
        st.session_state.transcription = ""
        st.session_state.summary = ""
        st.experimental_rerun()


if __name__ == "__main__":
    main()
