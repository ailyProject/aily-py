import os

from agishell.aigc import AIGC

aigc = AIGC('COM3')
aigc.set_temp(0.5)
aigc.init()


def event_handler(event):
    if event["type"] == "on_record_end":
        print("录音结束")
        aigc.send_message("你好")
    elif event["type"] == "wakeup":
        print("唤醒")
    elif event["type"] == "invoke_end":
        print("gpt调用完成")
        print("内容为: {0}".format(event["data"]))
    else:
        print(event)


aigc.event.subscribe(lambda i: event_handler(i))
aigc.run()
