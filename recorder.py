# recorder.py
import json
import nls
import sounddevice as sd
import time

class RealtimeMeetingRecorder:
    def __init__(self, url, aliyun_client):
        self.url = url
        self.aliyun_client = aliyun_client
        self.is_recording = False
        self.task_id = None
        self.meeting_join_url = None
        self.rm = None

    # 实现各种回调方法和录音逻辑
    def on_sentence_begin(self, message, *args):
        print("Sentence begin:", json.dumps(json.loads(message), indent=4, ensure_ascii=False))

    def on_sentence_end(self, message, *args):
        print("Sentence end:", json.dumps(json.loads(message), indent=4, ensure_ascii=False))
        sentence = json.loads(message)['payload']['result']
        print(sentence)
        return sentence
        # st.session_state.transcription += f"{sentence}\n"

    def on_result_changed(self, message, *args):
        print("Result changed:", json.dumps(json.loads(message), indent=4, ensure_ascii=False))

    def on_completed(self, message, *args):
        print("Completed:", json.dumps(json.loads(message), indent=4, ensure_ascii=False))

    def start_recording(self):
        self.is_recording = True
        task_response = self.aliyun_client.create_task(summarization_enabled=True)
        print("task创建完成")
        self.task_id = task_response[0]
        self.meeting_join_url = task_response[1]

        print(f"TaskId: {self.task_id}")
        print(f"MeetingJoinUrl: {self.meeting_join_url}")

        # 实现剩余的录音逻辑
        self.rm = nls.NlsRealtimeMeeting(
            url=self.meeting_join_url,
            on_sentence_begin=self.on_sentence_begin,
            on_sentence_end=self.on_sentence_end,
            on_result_changed=self.on_result_changed,
            on_completed=self.on_completed
        )

        self.rm.start()

        sample_rate = 16000
        samples_per_read = int(0.1 * sample_rate)

        with sd.InputStream(channels=1, dtype="int16", samplerate=sample_rate) as s:
            while self.is_recording:
                samples, _ = s.read(samples_per_read)
                self.rm.send_audio(samples.tobytes())
                time.sleep(0.01)

    def stop_recording(self):
        self.is_recording = False
        if self.rm is not None:
            self.rm.stop()
            self.rm = None
        if self.task_id:
            self.aliyun_client.stop_task(self.task_id)
            result = self.aliyun_client.get_result(self.task_id)
            return result
            # return result.get('Summarization', {}).get('Paragraph', '')
