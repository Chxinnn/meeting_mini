# recorder.py
import nls
import sounddevice as sd
import time
import threading

class RealtimeMeetingRecorder:
    def __init__(self, url, aliyun_client):
        self.url = url
        self.aliyun_client = aliyun_client
        self.is_recording = False
        self.task_id = None
        self.meeting_join_url = None

    # 实现各种回调方法和录音逻辑

    def start_recording(self):
        self.is_recording = True
        task_response = self.aliyun_client.create_task(summarization_enabled=True)
        print(task_response)
        print("task创建完成\n")
        self.task_id = task_response[0]
        self.meeting_join_url = task_response[1]

        print(f"TaskId: {self.task_id}")
        print(f"MeetingJoinUrl: {self.meeting_join_url}")

        # 实现剩余的录音逻辑
        # ...

    def stop_recording(self):
        self.is_recording = False
        if self.task_id:
            self.aliyun_client.stop_task(self.task_id)
            result = self.aliyun_client.get_result(self.task_id)
            return result
            # return result.get('Summarization', {}).get('Paragraph', '')
