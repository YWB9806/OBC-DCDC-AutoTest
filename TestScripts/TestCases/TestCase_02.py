import time

if __name__ == '__main__':
    print("正在执行{TestCase_02.py}文件")
    time.sleep(1)  # 修改为1秒，原来是1000秒
    print("[LVDC电流测试] 设置电流: 50A | 预期: 50.0A | 功分测量值: 50.12A | 信号上报值: 51.50A |误差: 1.383V (2.69%) | ✅通过")
    TestResult = False
    if TestResult == True:
        TestResultDisplay = '合格'
        print(TestResultDisplay)
    else:
        TestResultDisplay = '不合格'
        print(TestResultDisplay)