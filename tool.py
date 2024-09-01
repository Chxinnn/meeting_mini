import requests
import time
# 假设 json_result 是你已经获得的 JSON 数据

def req_head(json_result):
    autochapters_url = json_result.get('AutoChapters')
    if autochapters_url:
        response = requests.get(autochapters_url)
        if response.status_code == 200:
            autochapters_content = response.json()
            if 'AutoChapters' in autochapters_content:
                headline = autochapters_content['AutoChapters']
                return headline
            else:
                # 如果AutoChapters字段不存在，返回基于当前时间的唯一标识
                unique_id = f"unique_id_{int(time.time())}"
                return unique_id
        else:
            return "Failed to retrieve data from {autochapters_url}, status code: {response.status_code}"
    else:
        return "autochapters URL not found in json_result"
def req_summary(json_result):

    # 获取 Summarization URL
    summarization_url = json_result.get('Summarization')

    # 从URL中获取JSON内容
    if summarization_url:
        response = requests.get(summarization_url)
        if response.status_code == 200:
            summarization_content = response.json()
            speaker_summary = {
                item['SpeakerName']: item['Summary'] + '\n' 
                for item in summarization_content['Summarization']['ConversationalSummary']
            }
            # 将字典转换为字符串并去掉括号
            formatted_speaker_summary = "\n\n".join([f"{speaker}: {summary.strip()}" for speaker, summary in speaker_summary.items()])
            return formatted_speaker_summary
        else:
            return "Failed to retrieve data from {summarization_url}, status code: {response.status_code}"
    else:
        return "Summarization URL not found in json_result"