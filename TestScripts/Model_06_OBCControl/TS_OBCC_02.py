from CommonFunction.FunctionClass_V2 import *
from UtilityClass.UtilityClass01_DeviceConnectInit import *
from CommonFunction.Common00_Fuction import *
from CommonFunction.Common04_SoftwareCommonFunction import STLA_M_EncapsulationClass


if __name__ == '__main__':

    start_capture_prints()
    STLA_M_EncapsulationClass.InitDevice()
    STLA_M_EncapsulationClass.InitAllCANMessage()
    STLA_M_EncapsulationClass.TestCaseConfig(RecordStart = True, case_name = "STLA-M-VC2_TS_OBCC")
    低压辅源.SCPI.Write(':SOUR1:VOLT 12.5;:SOUR1:CURR 3;:OUTP CH1,ON')
    Sleep(8000)
    Test, MeasureKL30Current = 低压辅源.SCPI.Query(':MEAS:CURR? CH1')
    MeasureKL30Current = list(MeasureKL30Current)
    PreTestResult1 = MeasureKL30Current[0] <= 0.05
    print(MeasureKL30Current[0], PreTestResult1)

    STLA_CAN.DBC.SetSignal(1, get_message_for_signal('REVEIL_PRINCIPAL'), 'REVEIL_PRINCIPAL', 2)  
    低压辅源.SCPI.Write(':SOUR2:VOLT 5;:SOUR2:CURR 3;:OUTP CH2,ON')
    低压辅源.SCPI.Write(':SOUR3:VOLT 0.6;:SOUR3:CURR 3;:OUTP CH3,ON')
    信号发生器.SCPI.Write(':SOUR1:APPL:SQU 1000,12,0,0;:SOUR1:FUNC:SQU:DCYC 80;:OUTP1 ON')
    电阻控制板.Modbus.SetRegister(iID=1,Reg=3072,Data='220')
    STLA_CAN.DBC.SetSignal(1, get_message_for_signal('CABLE_LOCK_REQ'), 'CABLE_LOCK_REQ', 1)  
    Sleep(5000)
    交流源载一体机.Set.Basic(ACPwrModeEnum.SOUR, ACChannelEnum.EACH, ACCouplingEnum.AC,0, ACPwrWorkModeEnum.CC)
    交流源载一体机.Set.Freq(dFreq=50)
    交流源载一体机.Set.Volt(dealListData([230.0, 230.0, 230.0]),dealListData([0.0, 0.0, 0.0]))
    交流源载一体机.Out.Enable(ACeEnable.ON)
    高压源载一体机.Set.Basic(DCPwrModeEnum.NORM, DCPwrWorkModeEnum.NONE)
    高压源载一体机.Set.Volt(dVolt=365)
    高压源载一体机.Out.Enable(eEnable.ON)
    Sleep(5000)
    
    Test, OBCFaultState = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('OBC_FAULT_STATE'),'OBC_FAULT_STATE', 0.0)
    Test, AcdcConversionState = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('ACDC_CONVERSION_STATE'),'ACDC_CONVERSION_STATE', 0.0)
    Test, EvsePlugLockState = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('EVSE_PLUG_LOCK_STATE'),'EVSE_PLUG_LOCK_STATE', 0.0)
    PreTestResult2 = OBCFaultState == 0
    PreTestResult3 = AcdcConversionState == 0
    PreTestResult4 = EvsePlugLockState == 1
    PreCondition = True if PreTestResult1 and PreTestResult2 and PreTestResult3 and PreTestResult4 else False
    print(f"KL30电流测试结果: {PreTestResult1}, OBC故障状态测试结果: {PreTestResult2}, 交流直流转换状态测试结果: {PreTestResult3}, 充电枪锁止状态测试结果: {PreTestResult4}")

    all_results = {}
    test_ranges = [("0-475V", [(0, 475, 1)])]
    for name, voltage_ranges in test_ranges:
        all_results[name] = STLA_M_EncapsulationClass.TestHVDCVoltage_Standby(name, voltage_ranges)

    final_report = ""
    for name, results in all_results.items():
        final_report += STLA_M_EncapsulationClass.TestVoltage_GenerateResultString(name, results) + "\n\n"
    print(final_report)


    Sleep(5000)
    STLA_M_EncapsulationClass.TestCaseConfig(RecordStart = False, case_name = "STLA-M-VC2_TS_OBCC")
    STLA_M_EncapsulationClass.CloseAllCANMessage()
    STLA_M_EncapsulationClass.CloseAllDevice()

    Test, dArrTimeStamp1, dArrTimeStampList1 = STLA_CAN.DBC.FindValueOfSignal(get_message_for_signal('DCDC_REAL_HV_VOLT_HD'),'DCDC_REAL_HV_VOLT_HD',300,ConditionEnum.Morethan,0,0)
    Test, dArrTimeStamp2, dArrTimeStampList2 = STLA_CAN.DBC.FindValueOfSignal(get_message_for_signal('DCDC_REAL_HV_VOLT_HD'),'DCDC_REAL_HV_VOLT_HD',370,ConditionEnum.Morethan,0,0)
    Test, dArrTimeStamp3, dArrTimeStampList3 = STLA_CAN.DBC.FindValueOfSignal(get_message_for_signal('DCDC_REAL_HV_VOLT_HD'),'DCDC_REAL_HV_VOLT_HD',400,ConditionEnum.Morethan,0,0)
    Test, dArrTimeStamp4, dArrTimeStampList4 = STLA_CAN.DBC.FindValueOfSignal(get_message_for_signal('DCDC_REAL_HV_VOLT_HD'),'DCDC_REAL_HV_VOLT_HD',470,ConditionEnum.Morethan,0,0)
    Time1 = dArrTimeStamp1[10]
    Time2 = dArrTimeStamp2[10]
    Time3 = dArrTimeStamp3[10]
    Time4 = dArrTimeStamp4[10]

    CursorPosition = replace_zeros([Time1, Time2, Time3, Time4])
    signal_list = ['IFB_V_VerInfo6or13or20','IFB_Volt_KL30','IFB_Volt_KL15','IFB_Volt_LVCC','RCD_LINE_STATE',
                   'IFB_CCCP_CC_Res','OBC_FAULT_STATE','DCDC_FAULT_STATE','DCDC_REAL_HV_VOLT_HD']
    message_list = get_messages_for_signals(signal_list)
    STLA_CAN.DBC.ExportWfmFile(message_list,signal_list,'')
    Sleep(2000)
    STLA_CAN.DBC.ConfigureCursor(CursorEnum.X,CursorPosition)
    STLA_CAN.DBC.ExportImage(ImageFormatEnum.PNG,ColorInversionEnum.ON,'')


    failed_tests = [
        test_name 
        for test_name, results in all_results.items() 
        if False in results['is_pass']
    ]

    if not failed_tests:
        TestResult1 = True
        print("✅ 所有测试点均通过")
    else:
        TestResult1 = False
        print(f"❌ 失败的测试范围: {', '.join(failed_tests)}")

    print(f"前置条件结果: {PreCondition}, 测试步骤1结果: {TestResult1}")
    TestResult = True if PreCondition and TestResult1 else False
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
        f"1.The OBC output voltage is in the range of 0-475V, and the signal PItoHVConversion_HVVoltage(DCDC_REAL_HV_VOLT_HD) can be reported in real time\n"+
        f"\n"+
        f"Note:DC voltage ≤100V, detection accuracy: ±3V;\n"+
        f"Note:DC voltage > 100V, detection accuracy: ±3%\n"+
        f"\n"+
        f"========================================================================="+
        f"\n"+
        f"{all_prints}"
    )


