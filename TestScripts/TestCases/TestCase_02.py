import time

if __name__ == '__main__':
    print("正在执行{TestCase_02.py}文件")
    time.sleep(1)  # 修改为1秒，原来是1000秒

    TestResult = False
    if TestResult == True:
        TestResultDisplay = '合格'
        print(TestResultDisplay)
    else:
        TestResultDisplay = '不合格'
        print(TestResultDisplay)