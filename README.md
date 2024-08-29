# meeting_mini

a realtime meeting project

## 目标

实现一个会议语音记录与总结软件， 该软件能够通过音频设备获得现场发言者的声音，调用深度模型，进行语音识别； 调用摘要总结模型， 根据发言内容生成发言摘要。 软件选择“会议记录” 功能， 界面需要实时显示发言者语音识别内容；
选择总结摘要功能， 生成摘要； 具备基础的会议文本管理功能。 可选功能： 根据音色， 实时显示不同发言者的发言内容。

## 流程

- 创建记录任务-createTask，返回参数 MeetingJoinUrl
- 推流音频流，返回speaker_id,result
- 结束记录任务-stopTask，返回状态 TaskStatus
- 获取结果-getResult，返回URL链接

## config配置

- 创建 config.py 文件：在与 test.py 同一目录下创建一个名为 config.py 的文件
- 定义配置变量：在 config.py 文件中定义所需的配置变量
    ```
    # config.py
    
    # 阿里云访问密钥 ID
    ALIBABA_CLOUD_ACCESS_KEY_ID = "your_access_key_id_here"
    
    # 阿里云访问密钥 Secret
    ALIBABA_CLOUD_ACCESS_KEY_SECRET = "your_access_key_secret_here"
    
    # 应用密钥
    APP_KEY = "your_app_key_here"
    
    # NSL_URL
    NLS_URL = ""
    ```