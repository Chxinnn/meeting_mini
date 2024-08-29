# aliyun_client.py
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.auth.credentials import AccessKeyCredential
from aliyunsdkcore.request import CommonRequest
import json
import time

class AliyunClient:
    def __init__(self, access_key_id, access_key_secret, app_key, region_id='cn-beijing'):
        self.app_key = app_key
        credentials = AccessKeyCredential(access_key_id, access_key_secret)
        self.client = AcsClient(region_id=region_id, credential=credentials)

    def build_request(self, summarization_enabled, task_id, status):
        request = CommonRequest()
        request.set_accept_format('json')
        request.set_domain('tingwu.cn-beijing.aliyuncs.com')
        request.set_method('PUT')
        request.set_version('2023-09-30')
        request.set_protocol_type('https')
        request.set_uri_pattern('/openapi/tingwu/v2/tasks')
        if (status == 'get'):
            request.set_method('GET')
            request.set_uri_pattern( '/openapi/tingwu/v2/tasks' + '/' + task_id)
            return request
        if (status == 'start'):
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
        if (status == 'stop'):
            body = {
                'AppKey': self.app_key,
                'Input': {
                    'TaskId': task_id
                }
            }
            request.add_query_param('operation', 'stop')

        request.add_query_param('type', 'realtime')
        request.set_content(json.dumps(body).encode('utf-8'))
        return request
    
# TODO 加入异常处理类

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
        if response_json['Message'] == 'success':
            print("查询消息接收成功")
        task_status = response_json['Data']['TaskStatus']
        if(task_status == 'FAILED'):
            print('FAILED' + response_json['Data']['ErrorCode'] + response_json['Data']['ErrorMessage'])
        if(task_status == 'ONGOING' and not response_json['Data']['Result']):
            print("ONGOING BUT NOT RESULT")
            return None
        if(task_status == 'ONGOING' and response_json['Data']['Result']):
            print("ONGOING AND RESULT")
            return response_json['Data']['Result']
        if(task_status == 'COMPLETED'):
            print("COMPLETED")
            return response_json['Data']['Result']
        return None
