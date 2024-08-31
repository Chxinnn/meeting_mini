import config
from aliyun_client import AliyunClient
import json
from recorder import RealtimeMeetingRecorder
def main():
    aliyun_client = AliyunClient(
        access_key_id=config.ALIBABA_CLOUD_ACCESS_KEY_ID,
        access_key_secret=config.ALIBABA_CLOUD_ACCESS_KEY_SECRET,
        app_key=config.APP_KEY
    )
    #task_id, meeting_join_url = aliyun_client.create_task(False)
    #print(task_id, meeting_join_url)
    #task_status = aliyun_client.stop_task('391157f386a249dcafcf9067bd6a6870')
    #print(task_status)
    rmr = RealtimeMeetingRecorder(config.NLS_URL, aliyun_client)
    rmr.start_recording()


if __name__ == "__main__":
    main()
