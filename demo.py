import share_variable
import threading
import time

def main():
    # 修改全局变量
    share_variable.stopflag = True
    print("stopflag in demo.py:", share_variable.stopflag)  # 应该打印 True
    
    # 启动一个线程，并在其中再次修改 stopflag
    def thread_function():
        time.sleep(2)
        share_variable.stopflag = False
        print("stopflag in thread:", share_variable.stopflag)  # 应该打印 False
    
    threading.Thread(target=thread_function).start()
    time.sleep(3)
    print("stopflag after thread:", share_variable.stopflag)  # 应该打印 False

if __name__ == "__main__":
    main()