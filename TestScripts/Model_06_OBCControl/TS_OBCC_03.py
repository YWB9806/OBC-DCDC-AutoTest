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
    Sleep(5000)
    交流源载一体机.Set.Basic(ACPwrModeEnum.SOUR, ACChannelEnum.EACH, ACCouplingEnum.AC,0, ACPwrWorkModeEnum.CC)
    交流源载一体机.Set.Freq(dFreq=50)
    交流源载一体机.Set.Volt(dealListData([230.0, 230.0, 230.0]),dealListData([0.0, 0.0, 0.0]))
    交流源载一体机.Out.Enable(ACeEnable.ON)
    高压源载一体机.Set.Basic(DCPwrModeEnum.NORM, DCPwrWorkModeEnum.NONE)
    高压源载一体机.Set.Volt(dVolt=190)
    高压源载一体机.Out.Enable(eEnable.ON)
    Sleep(5000)
    Test, OBCFaultState = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('OBC_FAULT_STATE'),'OBC_FAULT_STATE', 0.0)
    Test, AcdcConversionState = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('ACDC_CONVERSION_STATE'),'ACDC_CONVERSION_STATE', 0.0)
    PreTestResult2 = OBCFaultState == 0
    PreTestResult3 = AcdcConversionState == 0
    PreCondition1 = True if PreTestResult1 and PreTestResult2 and PreTestResult3 else False
    print(f"KL30电流测试结果: {PreTestResult1}, OBC故障状态测试结果: {PreTestResult2}, 交流直流转换状态测试结果: {PreTestResult3}")

    STLA_CAN.DBC.SetSignal(1, get_message_for_signal('CABLE_LOCK_REQ'), 'CABLE_LOCK_REQ', 1)  
    STLA_CAN.DBC.SetSignal(1, get_message_for_signal('OBC_EVSE_REQUEST'), 'OBC_EVSE_REQUEST', 1)  
    STLA_CAN.DBC.SetSignal(1, get_message_for_signal('MAX_INDI_CHRG_CURR'), 'MAX_INDI_CHRG_CURR', -40)  
    STLA_CAN.DBC.SetSignal(1, get_message_for_signal('HV_CHRG_CURR_REG_MODE_SP'), 'HV_CHRG_CURR_REG_MODE_SP', 40)  
    Sleep(2000)
    Test, EvsePlugLockState = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('EVSE_PLUG_LOCK_STATE'),'EVSE_PLUG_LOCK_STATE', 0.0)
    Test, OBC_EVSE_State = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('OBC_EVSE_STATE'),'OBC_EVSE_STATE', 0.0)
    PreTestResult4 = EvsePlugLockState == 1
    PreTestResult5 = OBC_EVSE_State == 5
    PreCondition2 = True if PreTestResult4 and PreTestResult5 and PreTestResult3 else False
    print(f"EVSE锁状态测试结果: {PreTestResult4}, OBC EVSE状态测试结果: {PreTestResult5}")

    STLA_CAN.DBC.SetSignal(1, get_message_for_signal('ACDC_CONVERSION_REQUEST'), 'ACDC_CONVERSION_REQUEST', 2)  
    Sleep(2000)
    Test, AcdcConversionState = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('ACDC_CONVERSION_STATE'),'ACDC_CONVERSION_STATE', 0.0)
    PreCondition3 = AcdcConversionState == 3
    PreCondition = True if PreCondition1 and PreCondition2 and PreCondition3 else False

    test_configs = [
        {
            "name": "HVDC电流测试",
            "voltages": [275, 300, 350, 400, 450, 465],
            "currents": [-38.5, -35.3, -30.3, -26.5, -23.6, -22.8]
        },
    ]

    all_results = {}
    for config in test_configs:
        results, report, passed = STLA_M_EncapsulationClass.TestHVDCCurrent_VoltageRegulation(
            config["voltages"],
            config["currents"],
            'OBC_DCDC_HV_CURRENT',
            config["name"]
        )
        all_results[config["name"]] = {"results": results,"report": report,"overall_pass": passed}
        print("\n" + report)

    Sleep(5000)
    STLA_M_EncapsulationClass.TestCaseConfig(RecordStart = False, case_name = "STLA-M-VC2_TS_OBCC")
    STLA_M_EncapsulationClass.CloseAllCANMessage()
    STLA_M_EncapsulationClass.CloseAllDevice()

    Test, dArrTimeStamp1, dArrTimeStampList1 = STLA_CAN.DBC.FindValueOfSignal(get_message_for_signal('DCDC_REAL_HV_VOLT_HD'),'DCDC_REAL_HV_VOLT_HD',270,ConditionEnum.Morethan,0,0)
    Test, dArrTimeStamp2, dArrTimeStampList2 = STLA_CAN.DBC.FindValueOfSignal(get_message_for_signal('DCDC_REAL_HV_VOLT_HD'),'DCDC_REAL_HV_VOLT_HD',300,ConditionEnum.Morethan,0,0)
    Test, dArrTimeStamp3, dArrTimeStampList3 = STLA_CAN.DBC.FindValueOfSignal(get_message_for_signal('DCDC_REAL_HV_VOLT_HD'),'DCDC_REAL_HV_VOLT_HD',400,ConditionEnum.Morethan,0,0)
    Test, dArrTimeStamp4, dArrTimeStampList4 = STLA_CAN.DBC.FindValueOfSignal(get_message_for_signal('DCDC_REAL_HV_VOLT_HD'),'DCDC_REAL_HV_VOLT_HD',460,ConditionEnum.Morethan,0,0)
    Time1 = dArrTimeStamp1[10]
    Time2 = dArrTimeStamp2[10]
    Time3 = dArrTimeStamp3[10]
    Time4 = dArrTimeStamp4[10]

    CursorPosition = replace_zeros([Time1, Time2, Time3, Time4])
    signal_list = ['IFB_V_VerInfo6or13or20','IFB_Volt_KL30','IFB_Volt_KL15','IFB_Volt_LVCC','RCD_LINE_STATE',
                   'IFB_CCCP_CC_Res','OBC_FAULT_STATE','DCDC_FAULT_STATE','OBC_DCDC_HV_CURRENT','OBC_EVSE_STATE','OBC_EVSE_REQUEST','OBC_CHRG_CONN_CONF',
                   'ACDC_CONVERSION_STATE','CABLE_LOCK_REQ','ACDC_CONVERSION_REQUEST','EVSE_PLUG_LOCK_STATE']
    message_list = get_messages_for_signals(signal_list)
    STLA_CAN.DBC.ExportWfmFile(message_list,signal_list,'')
    Sleep(2000)
    STLA_CAN.DBC.ConfigureCursor(CursorEnum.X,CursorPosition)
    STLA_CAN.DBC.ExportImage(ImageFormatEnum.PNG,ColorInversionEnum.ON,'')

    final_report = "HVDC电流测试最终汇总\n" + "="*100 + "\n"
    for test_name, data in all_results.items():
        final_report += f"\n▶ {test_name}: {'✅通过' if data['overall_pass'] else '❌失败'}\n"
        final_report += data['report']

    if all(data["overall_pass"] for data in all_results.values()):
        TestResult1 = True
        print("\n🔥 所有测试组均通过")
    else:
        TestResult1 = False
        failed_tests = [name for name, data in all_results.items() if not data["overall_pass"]]
        print(f"\n🚨 存在失败测试组: {', '.join(failed_tests)}")

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
        f"1. OBC can run normally,and PItoHVConversion_HVCurrent(OBC_DCDC_HV_CURRENT) is 38.5A/35.3A/30.3A/26.5A//23.0A/22.8A \n"+
        f"\n"+
        f"Note:Output current ≤4A, detection accuracy: ± 200mA;\n"+
        f"Note:Output current >4A, detection accuracy: ± 5%\n"+
        f"\n"+
        f"========================================================================="+
        f"\n"+
        f"{all_prints}"
    )


