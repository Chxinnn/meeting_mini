import requests

# 假设 json_result 是你已经获得的 JSON 数据

def req_summary(json_result):

    # 获取 Summarization URL
    summarization_url = json_result.get('Summarization')

    # 从URL中获取JSON内容
    if summarization_url:
        response = requests.get(summarization_url)
        if response.status_code == 200:
            summarization_content = response.json()
            speaker_summary = {item['SpeakerName']: item['Summary'] for item in summarization_content['Summarization']['ConversationalSummary']}
            return speaker_summary
        else:
            return "Failed to retrieve data from {summarization_url}, status code: {response.status_code}"
    else:
        return "Summarization URL not found in json_result"