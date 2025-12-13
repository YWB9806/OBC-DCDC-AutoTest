from CommonFunction.FunctionClass_V2 import *
from UtilityClass.UtilityClass01_DeviceConnectInit import *
from CommonFunction.Common00_Fuction import *
from CommonFunction.Common04_SoftwareCommonFunction import STLA_M_EncapsulationClass


if __name__ == '__main__':

    start_capture_prints()
    STLA_M_EncapsulationClass.InitDevice()
    STLA_M_EncapsulationClass.InitAllCANMessage()
    STLA_M_EncapsulationClass.TestCaseConfig(RecordStart = True, case_name = "STLA-M-VC2_TS_DCC")
    低压辅源.SCPI.Write(':SOUR1:VOLT 12.5;:SOUR1:CURR 3;:OUTP CH1,ON')
    Sleep(8000)
    Test, MeasureKL30Current = 低压辅源.SCPI.Query(':MEAS:CURR? CH1')
    MeasureKL30Current = list(MeasureKL30Current)
    PreTestResult1 = MeasureKL30Current[0] <= 0.05
    print(f"KL30电流:{MeasureKL30Current[0]},测试结果:{PreTestResult1}")

    STLA_CAN.DBC.SetSignal(1, get_message_for_signal('REVEIL_PRINCIPAL'), 'REVEIL_PRINCIPAL', 2)  
    低压辅源.SCPI.Write(':SOUR2:VOLT 5;:SOUR2:CURR 3;:OUTP CH2,ON')
    低压辅源.SCPI.Write(':SOUR3:VOLT 0.6;:SOUR3:CURR 3;:OUTP CH3,ON')
    电阻控制板.Modbus.SetRegister(iID=1,Reg=3072,Data='220')

    STLA_CAN.DBC.SetSignal(1, get_message_for_signal('VOLT_SETPOINT_DCDC_REQ'), 'VOLT_SETPOINT_DCDC_REQ', 15)  
    STLA_CAN.DBC.SetSignal(1, get_message_for_signal('CURR_SETPOINT_DCDC_LV_REQ'), 'CURR_SETPOINT_DCDC_LV_REQ', 250)  

    高压源载一体机.Set.Basic(DCPwrModeEnum.NORM, DCPwrWorkModeEnum.NONE)
    高压源载一体机.Set.Volt(dVolt=365)
    高压源载一体机.Set.Curr(DCPwrSLEnum.SOUR, 15)
    高压源载一体机.Out.Enable(eEnable.ON)
    Sleep(5000)  
    Test, DCDCFaultState = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('DCDC_FAULT_STATE'),'DCDC_FAULT_STATE', 0.0)
    Test, DCDCStateBB1 = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('DCDC_STATE_BB'),'DCDC_STATE_BB', 0.0)
    Sleep(5000)
    PreTestResult2 = DCDCFaultState == 0
    PreTestResult3 = DCDCStateBB1 == 2
    PreCondition = True if PreTestResult1 and PreTestResult2 and PreTestResult3 else False
    print(f"DCDC故障状态:{DCDCFaultState},测试结果:{PreTestResult2}")
    print(f"DCDC状态:{DCDCFaultState},测试结果:{PreTestResult3}")
    
    低压源载一体机.Set.Basic(DCPwrModeEnum.NORM, DCPwrWorkModeEnum.NONE)
    低压源载一体机.Set.Volt(dVolt=4)
    低压源载一体机.Out.Enable(eEnable.ON)
    Sleep(5000)
    Test, signal_voltage1 = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('DCDC_CONV_LV_VOLT_HD'),'DCDC_CONV_LV_VOLT_HD', 0.0)
    低压源载一体机.Set.Volt(dVolt=21.5)
    Sleep(5000)
    Test, signal_voltage2 = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('DCDC_CONV_LV_VOLT_HD'),'DCDC_CONV_LV_VOLT_HD', 0.0)
    TestResult11 = abs(signal_voltage1 - 4) <= 0.2
    TestResult12 = abs(signal_voltage2 - 21.5) <= 0.2
    TestResult1 = TestResult11 and TestResult12
    print(f"DCDC电压1:{signal_voltage1},测试结果1:{TestResult11}")
    print(f"DCDC电压2:{signal_voltage2},测试结果2:{TestResult12}")

    STLA_CAN.DBC.SetSignal(1, get_message_for_signal('VOLT_SETPOINT_DCDC_REQ'), 'VOLT_SETPOINT_DCDC_REQ', 14)  
    STLA_CAN.DBC.SetSignal(1, get_message_for_signal('REG_MODE_DCDC_BB_REQ'), 'REG_MODE_DCDC_BB_REQ', 2)  
    Sleep(5000)
    低压源载一体机.Set.Basic(DCPwrModeEnum.NORM, DCPwrWorkModeEnum.NONE)
    低压源载一体机.Set.Volt(dVolt=14)
    低压源载一体机.Set.Curr(DCPwrSLEnum.LOAD, 0)
    Sleep(5000)
    Test, signal_current1 = STLA_CAN.DBC.GetSignal(1, get_message_for_signal('DCDC_REAL_LV_CURR_HD'),'DCDC_REAL_LV_CURR_HD', 0.0)
    低压源载一体机.Set.Curr(DCPwrSLEnum.LOAD, 250)
    低压源载一体机.Out.Enable(eEnable.ON)
    Sleep(5000)
    Test, signal_current2 = STLA_CAN.DBC.GetSignal(1, get_message_for_signal('DCDC_REAL_LV_CURR_HD'),'DCDC_REAL_LV_CURR_HD', 0.0)
    Test, measure_current = 功率分析仪.Meas.Curr(PACurrEnum.RMS, dealListData([0]*8))
    measure_current = list(measure_current)[4]
    TestResult21 = abs(signal_current1 - 0) <= 5
    TestResult22 = abs(measure_current - signal_current2) <= 5
    TestResult2 = TestResult21 and TestResult22
    print(f"DCDC电流信号1:{signal_current1},测试结果:{TestResult21}")
    print(f"功率分析仪测量电流:{measure_current}")
    print(f"DCDC电流信号2:{signal_current2},测试结果:{TestResult22}")

    STLA_CAN.DBC.SetSignal(1, get_message_for_signal('REG_MODE_DCDC_BB_REQ'), 'REG_MODE_DCDC_BB_REQ', 0)  
    Sleep(5000)

    all_results = {}
    test_ranges = [("171-465V", [(171, 465, 20)])]
    for name, voltage_ranges in test_ranges:
        all_results[name] = STLA_M_EncapsulationClass.TestHVDCVoltage_Standby(name, voltage_ranges)

    final_report = ""
    for name, results in all_results.items():
        final_report += STLA_M_EncapsulationClass.TestVoltage_GenerateResultString(name, results) + "\n\n"
    print(final_report)

    failed_tests = [
        test_name 
        for test_name, results in all_results.items() 
        if False in results['is_pass']
    ]
    if not failed_tests:
        TestResult1 = True
        print("✅ 所有测试点均通过")
    else:
        TestResult2 = False
        print(f"❌ 失败的测试范围: {', '.join(failed_tests)}")

    高压源载一体机.Set.Volt(dVolt=365)
    Sleep(5000)
    StartTime = TimeStamp()     # 获取毫秒级时间戳
    高压源载一体机.Set.Volt(dVolt=480)
    Sleep(5000)
    Test, DCDCHVOverVoltage = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('DCDC_HV_OVERVOLT'),'DCDC_HV_OVERVOLT', 0.0)
    TestResult3 = DCDCHVOverVoltage == 1
    print(f"DCDC_HV_OVERVOLT:{DCDCHVOverVoltage},测试结果:{TestResult3}")
    高压源载一体机.Set.Volt(dVolt=365)
    Sleep(5000)

    低压源载一体机.Set.Volt(dVolt=19)
    Sleep(5000)
    Test, DCDCLVOverVoltage = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('DCDC_LV_OVERVOLT'),'DCDC_LV_OVERVOLT', 0.0)
    TestResult4 = DCDCLVOverVoltage == 1
    print(f"DCDC_LV_OVERVOLT:{DCDCLVOverVoltage},测试结果:{TestResult4}")

    Sleep(5000)
    STLA_M_EncapsulationClass.TestCaseConfig(RecordStart = False, case_name = "STLA-M-VC2_TS_DCC")
    STLA_M_EncapsulationClass.CloseAllCANMessage()
    STLA_M_EncapsulationClass.CloseAllDevice()
    
    Test, dArrTimeStamp1, dArrTimeStampList1 = STLA_CAN.DBC.FindValueOfSignal(get_message_for_signal('DCDC_HV_OVERVOLT'),'DCDC_HV_OVERVOLT',1,ConditionEnum.Equal,StartTime,0)
    Test, dArrTimeStamp2, dArrTimeStampList2 = STLA_CAN.DBC.FindValueOfSignal(get_message_for_signal('DCDC_LV_OVERVOLT'),'DCDC_LV_OVERVOLT',1,ConditionEnum.Equal,StartTime,0)
    Time1 = dArrTimeStamp1[0]
    Time2 = dArrTimeStamp2[0]

    CursorPosition = replace_zeros([Time1, Time2])
    signal_list = ['IFB_V_VerInfo6or13or20','IFB_Volt_KL30','IFB_Volt_KL15','IFB_Volt_LVCC','RCD_LINE_STATE',
                   'IFB_CCCP_CC_Res','OBC_FAULT_STATE','DCDC_FAULT_STATE','LD_IORpt_LvCur','REG_MODE_DCDC_BB_REQ','DCDC_STATE_BB',
                   'LD_IORpt_LvVol','DCDC_HV_OVERVOLT','DCDC_LV_OVERVOLT']
    message_list = get_messages_for_signals(signal_list)
    STLA_CAN.DBC.ExportWfmFile(message_list,signal_list,'')
    Sleep(2000)
    STLA_CAN.DBC.ConfigureCursor(CursorEnum.X,CursorPosition)
    STLA_CAN.DBC.ExportImage(ImageFormatEnum.PNG,ColorInversionEnum.ON,'')

    print(f"前置条件结果: {PreCondition}, 测试步骤1结果: {TestResult1}, 测试步骤2结果: {TestResult2}, 测试步骤3结果: {TestResult3}, 测试步骤4结果: {TestResult4}")
    TestResult = True if PreCondition and TestResult1 and TestResult2 and TestResult3 and TestResult4 else False
    if TestResult == True:
        TestResultDisplay = '合格'
        Log4NetWrapper.WriteToOutput(f'测试结果:{TestResultDisplay}')
        print(TestResultDisplay)
    else:
        TestResultDisplay = '不合格'
        Log4NetWrapper.WriteToOutput(f'测试结果:{TestResultDisplay}')
        print(TestResultDisplay)
    
    all_prints = stop_capture_prints()
    Log4NetWrapper.WriteToOutput_KeyInfo(TestResultDisplay, 
        f"\n"+
        f"1.  DCDC output voltage is [ 4V , 21.5V].\n"+
        f"2.  DCDC output current is [ 0A, 250A].\n"+
        f"3.  DCDC input voltage is [ 171V,  465V].\n"+
        f"4.  DCDC_HV_OVERVOLT=HV  overvoltage.\n"+
        f"5.  DCDC_LV_OVERVOLT= LV  overvoltage.\n"+
        f"\n"+
        f"Note: Output current accuracy\n"+
        f"========================================================================="+
        f"\n"+
        f"{all_prints}"
    )













