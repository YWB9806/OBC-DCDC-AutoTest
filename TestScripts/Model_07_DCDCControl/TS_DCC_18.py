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
    高压源载一体机.Set.Basic(DCPwrModeEnum.NORM, DCPwrWorkModeEnum.NONE)
    高压源载一体机.Set.Volt(dVolt=375)
    高压源载一体机.Out.Enable(eEnable.ON)
    Sleep(5000)  
    Test, DCDCFaultState = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('DCDC_FAULT_STATE'),'DCDC_FAULT_STATE', 0.0)
    Test, DCDCStateBB1 = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('DCDC_STATE_BB'),'DCDC_STATE_BB', 0.0)
    Sleep(5000)
    STLA_CAN.DBC.SetSignal(1, get_message_for_signal('REG_MODE_DCDC_BB_REQ'), 'REG_MODE_DCDC_BB_REQ', 1)  
    Sleep(1000)
    Test, DCDCStateBB2 = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('DCDC_STATE_BB'),'DCDC_STATE_BB', 0.0)
    PreTestResult2 = DCDCFaultState == 0
    PreTestResult3 = DCDCStateBB1 == 2
    PreTestResult4 = DCDCStateBB2 == 3
    PreCondition = True if PreTestResult1 and PreTestResult2 and PreTestResult3 and PreTestResult4 else False
    print(f"DCDC故障状态:{DCDCFaultState},测试结果:{PreTestResult2}")
    print(f"DCDC状态1:{DCDCFaultState},测试结果:{PreTestResult3}")
    print(f"DCDC状态2:{DCDCFaultState},测试结果:{PreTestResult4}")
    
    test_configs = [
        {
            "name": "HVDC电压测试",
            "setvoltages": [171, 220, 300, 375, 400, 465],
            "expectvoltages": [171, 220, 300, 375, 400, 465]
        },
    ]

    all_results = {}
    for config in test_configs:
        results, report, passed = STLA_M_EncapsulationClass.TestHVDCVoltage_VoltageRegulation(
            config["name"],
            config["setvoltages"],
            config["expectvoltages"]
        )
        all_results[config["name"]] = {"results": results,"report": report,"overall_pass": passed}
        print("\n" + report)


    Sleep(5000)
    STLA_M_EncapsulationClass.TestCaseConfig(RecordStart = False, case_name = "STLA-M-VC2_TS_DCC")
    STLA_M_EncapsulationClass.CloseAllCANMessage()
    STLA_M_EncapsulationClass.CloseAllDevice()

    Test, dArrTimeStamp0, dArrTimeStampList0 = STLA_CAN.DBC.FindValueOfSignal(get_message_for_signal('DCDC_REAL_HV_VOLT_HD'),'DCDC_REAL_HV_VOLT_HD',200,ConditionEnum.Lessthan,0,0)
    Time0 = dArrTimeStamp0[0]
    
    Test, dArrTimeStamp1, dArrTimeStampList1 = STLA_CAN.DBC.FindValueOfSignal(get_message_for_signal('DCDC_REAL_HV_VOLT_HD'),'DCDC_REAL_HV_VOLT_HD',170,ConditionEnum.Morethan,Time0,0)
    Test, dArrTimeStamp2, dArrTimeStampList2 = STLA_CAN.DBC.FindValueOfSignal(get_message_for_signal('DCDC_REAL_HV_VOLT_HD'),'DCDC_REAL_HV_VOLT_HD',300,ConditionEnum.Morethan,Time0,0)
    Test, dArrTimeStamp3, dArrTimeStampList3 = STLA_CAN.DBC.FindValueOfSignal(get_message_for_signal('DCDC_REAL_HV_VOLT_HD'),'DCDC_REAL_HV_VOLT_HD',400,ConditionEnum.Morethan,Time0,0)
    Test, dArrTimeStamp4, dArrTimeStampList4 = STLA_CAN.DBC.FindValueOfSignal(get_message_for_signal('DCDC_REAL_HV_VOLT_HD'),'DCDC_REAL_HV_VOLT_HD',450,ConditionEnum.Morethan,Time0,0)
    Time1 = dArrTimeStamp1[0]
    Time2 = dArrTimeStamp2[0]
    Time3 = dArrTimeStamp3[0]
    Time4 = dArrTimeStamp4[0]

    CursorPosition = replace_zeros([Time1, Time2, Time3, Time4])
    signal_list = ['IFB_V_VerInfo6or13or20','IFB_Volt_KL30','IFB_Volt_KL15','IFB_Volt_LVCC','RCD_LINE_STATE',
                   'IFB_CCCP_CC_Res','OBC_FAULT_STATE','DCDC_FAULT_STATE','L_IORpt_HvVol','REG_MODE_DCDC_BB_REQ','DCDC_STATE_BB']
    message_list = get_messages_for_signals(signal_list)
    STLA_CAN.DBC.ExportWfmFile(message_list,signal_list,'')
    Sleep(2000)
    STLA_CAN.DBC.ConfigureCursor(CursorEnum.X,CursorPosition)
    STLA_CAN.DBC.ExportImage(ImageFormatEnum.PNG,ColorInversionEnum.ON,'')


    final_report = "HVDC电压测试最终汇总\n" + "="*100 + "\n"
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
        f"1. DCDC entes BUCK mode, and input voltage is reported in real time with 171V/220V/300V/375V/400V/465V.\n"+
        f"\n"+
        f"Note:DC voltage ≤100V, detection accuracy: ±3V;\n"+
        f"Note:DC voltage > 100V, detection accuracy: ±3%\n"+
        f"\n"+
        f"========================================================================="+
        f"\n"+
        f"{all_prints}"
    )

