import config
from aliyun_client import AliyunClient
import json
def main():
    aliyun_client = AliyunClient(
        access_key_id=config.ALIBABA_CLOUD_ACCESS_KEY_ID,
        access_key_secret=config.ALIBABA_CLOUD_ACCESS_KEY_SECRET,
        app_key=config.APP_KEY
    )
    # task_id, meeting_join_url = aliyun_client.create_task(False)
    # print(task_id, meeting_join_url)
    #task_status = aliyun_client.stop_task('391157f386a249dcafcf9067bd6a6870')
    #print(task_status)
    result = aliyun_client.get_result('391157f386a249dcafcf9067bd6a6870')
    print(json.dumps(result))


if __name__ == "__main__":
    main()
