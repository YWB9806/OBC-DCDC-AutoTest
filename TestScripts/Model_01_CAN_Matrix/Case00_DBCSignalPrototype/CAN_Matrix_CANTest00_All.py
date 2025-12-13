import cantools
import pandas as pd
from CommonFunction.FunctionClass_V2 import Log4NetWrapper
from CommonFunction.Common00_Fuction import *

if __name__ == '__main__':

    db = cantools.database.load_file("D:\\项目资料\\04_STLA_XS\\STLA-XS-VF4.0\\01552_24_02170_DBC_FD_CAN5_IDCM_ENTRY_STLAS_V3.0.dbc")
    # 加载数据
    # STLA_XS_CAN_Matrix_Datasets = pd.read_csv("D:/AI自动化/DriverTest/TestSequence_STLA_XS/Data/STLA_XS_CAN_Matrix.csv", encoding='utf-8')
    # STLA_XS_CAN_Matrix_Datasets = pd.read_excel("D:\\项目资料\\04_STLA_XS\\STLA-XS-VF4.0\\VF4.0测试用例\\STLA_XS_CAN_Matrix.xlsx",sheet_name='测试用例Test Case_CAN Matrix')
    STLA_XS_CAN_Matrix_Datasets = pd.read_excel("D:\\项目资料\\04_STLA_XS\\STLA-XS-VF4.0\\VF4.0测试用例\\EVTECH_STLA-XS_V1.2_CAN_Matrix_复测_2.xlsx",sheet_name='测试用例Test Case_CAN Matrix')
    # 将"Not applicable"替换为None
    # STLA_XS_CAN_Matrix_Datasets.replace("Not applicable", None, inplace=True)


    # 遍历每一行数据
    i = 2
    for i in range(len(STLA_XS_CAN_Matrix_Datasets)):

        Log4NetWrapper.InitLogManage("STLA-XS-VF4.0-CAN_Matrix", STLA_XS_CAN_Matrix_Datasets.iloc[i, 4])

        # --- 处理第2列（Test Case Name）的分割 ---
        # test_case_name = STLA_XS_CAN_Matrix_Datasets.iloc[i, 1]  # 第2列（索引为1）
        test_case_name = STLA_XS_CAN_Matrix_Datasets.iloc[i, 5]  # 第5列（索引为5）
        # print(f"第{i}行Test Case ID: {STLA_XS_CAN_Matrix_Datasets.iloc[i, 4]}")

        # 按第一个'-'分割为前后两部分
        if '-' in test_case_name:
            message_name, signal_name = test_case_name.split('-', 1)
            # print(f"第{i}行报文名称: {message_name}, 信号名称: {signal_name}")
        else:
            # print(f"第{i}行Test Case Name格式错误: {test_case_name}")
            continue  # 跳过格式错误的数据
        
        # 提取从第3列开始的7个字段
        # row_data = STLA_XS_CAN_Matrix_Datasets.iloc[i, 2:9].tolist()
        row_data = STLA_XS_CAN_Matrix_Datasets.iloc[i, 10:17].tolist()
        # 解包赋值给目标变量
        (ExpectOfSignalBytePosition, ExpectOfSignalBitPosition, ExpectOfSignalLength, ExpectOfSignalPhyMinValue,
         ExpectOfSignalPhyMaxValue, ExpectOfSignalPhyResolution, ExpectOfSignalPhyOffset) = row_data
        
        try:
            message = db.get_message_by_name(message_name)
            signal = message.get_signal_by_name(signal_name)
            RealTestOfSignalBytePosition, RealTestOfSignalBitPosition = calculate_motorola_position(signal.start, signal.length)   

            # 初始化所有测试结果为True（默认不参与校验的项视为通过）
            TestResult11 = TestResult12 = TestResult13 = TestResult14 = TestResult15 = TestResult16 = TestResult17 = True

            # --- 动态判断每个测试项 ---
            # 只有期望值不为None时才进行比较
            if ExpectOfSignalBytePosition != "Not applicable" or ExpectOfSignalBytePosition != "Not Applicable":
                TestResult11 = (float(ExpectOfSignalBytePosition) == float(RealTestOfSignalBytePosition))
            if ExpectOfSignalBitPosition != "Not applicable" or ExpectOfSignalBytePosition != "Not Applicable":
                TestResult12 = (float(ExpectOfSignalBitPosition) == float(RealTestOfSignalBitPosition))
            if ExpectOfSignalLength != "Not applicable" or ExpectOfSignalBytePosition != "Not Applicable":
                TestResult13 = (float(ExpectOfSignalLength) == float(signal.length))
            if ExpectOfSignalPhyMinValue != "Not applicable" or ExpectOfSignalBytePosition != "Not Applicable":
                TestResult14 = (float(ExpectOfSignalPhyMinValue) == float(signal.minimum))
            if ExpectOfSignalPhyMaxValue != "Not applicable" or ExpectOfSignalBytePosition != "Not Applicable":
                TestResult15 = (float(ExpectOfSignalPhyMaxValue) == float(signal.maximum))
            if ExpectOfSignalPhyResolution != "Not applicable" or ExpectOfSignalBytePosition != "Not Applicable":
                TestResult16 = (float(ExpectOfSignalPhyResolution) == float(signal.scale))
            if ExpectOfSignalPhyOffset != "Not applicable" or ExpectOfSignalBytePosition != "Not Applicable":
                TestResult17 = (float(ExpectOfSignalPhyOffset) == float(signal.offset))

            # --- 计算最终结果（仅当所有非None项通过时，总结果为True）---
            TestResult = all([TestResult11, TestResult12, TestResult13, TestResult14, TestResult15, TestResult16, TestResult17])
            if TestResult == True:
                Log4NetWrapper.WriteToOutput(f'测试ID:{STLA_XS_CAN_Matrix_Datasets.iloc[i, 4]}')
                TestResultDisplay = '合格'
                Log4NetWrapper.WriteToOutput(f'测试结果:{TestResultDisplay}')
                print(f"第{i}行, {STLA_XS_CAN_Matrix_Datasets.iloc[i, 5]} 测试结果: {TestResultDisplay}")
            else:
                Log4NetWrapper.WriteToOutput(f'测试ID:{STLA_XS_CAN_Matrix_Datasets.iloc[i, 4]}')
                TestResultDisplay = '不合格'
                Log4NetWrapper.WriteToOutput(f'测试结果:{TestResultDisplay}')
                print(f"第{i}行, {STLA_XS_CAN_Matrix_Datasets.iloc[i, 5]} 测试结果: {TestResultDisplay}")

            Log4NetWrapper.WriteToOutput(f'$报文名称:{message_name},信号名称:{signal.name}#\n')
            Log4NetWrapper.WriteToOutput(f'$预期信号字节位置: {ExpectOfSignalBytePosition}，实测信号字节位置：{RealTestOfSignalBytePosition}，测试结果:{TestResult11}')
            Log4NetWrapper.WriteToOutput(f'$预期信号比特位置: {ExpectOfSignalBitPosition}，实测信号比特位置：{RealTestOfSignalBitPosition}，测试结果:{TestResult12}')
            Log4NetWrapper.WriteToOutput(f'$预期信号长度: {ExpectOfSignalLength}，实测信号长度{signal.length}，测试结果:{TestResult13}')
            Log4NetWrapper.WriteToOutput(f'$预期信号最小值: {ExpectOfSignalPhyMinValue}，实测信号最小值: {signal.minimum}，测试结果:{TestResult14}')
            Log4NetWrapper.WriteToOutput(f'$预期信号最大值: {ExpectOfSignalPhyMaxValue}，实测信号最大值: {signal.maximum}，测试结果:{TestResult15}')
            Log4NetWrapper.WriteToOutput(f'$预期信号因子: {ExpectOfSignalPhyResolution}，实测信号因子: {signal.scale}，测试结果:{TestResult16}')
            Log4NetWrapper.WriteToOutput(f'$预期信号偏移: {ExpectOfSignalPhyOffset}，实测信号偏移: {signal.offset}，测试结果:{TestResult17}')
            Log4NetWrapper.WriteToOutput(f'==============================================')
            Sleep(1000)

        except Exception as e:
            Log4NetWrapper.WriteToOutput(f'测试ID:{STLA_XS_CAN_Matrix_Datasets.iloc[i, 4]}')
            TestResultDisplay = '不合格'
            Log4NetWrapper.WriteToOutput(f'测试结果:{TestResultDisplay}')
            print(f"第{i}行, {STLA_XS_CAN_Matrix_Datasets.iloc[i, 5]} 测试结果: {TestResultDisplay}")
            Log4NetWrapper.WriteToOutput(f'=======================')
            Sleep(1000)
