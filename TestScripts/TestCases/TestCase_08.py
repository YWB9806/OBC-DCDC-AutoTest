import time

if __name__ == '__main__':
    print("正在执行{TestCase_08.py}文件")
    time.sleep(1)

    TestResult = True 
    if TestResult == True:
        TestResultDisplay = '合格'
        print(TestResultDisplay)
    else:
        TestResultDisplay = '不合格'
        print(TestResultDisplay)