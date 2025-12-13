from CommonFunction.FunctionClass_V2 import *
from UtilityClass.UtilityClass01_DeviceConnectInit import *
from CommonFunction.Common00_Fuction import *
from CommonFunction.Common04_SoftwareCommonFunction import STLA_M_EncapsulationClass

if __name__ == '__main__':

    start_capture_prints()
    STLA_M_EncapsulationClass.InitDevice()
    STLA_M_EncapsulationClass.InitAllCANMessage()
    STLA_M_EncapsulationClass.TestCaseConfig(RecordStart = True, case_name = "STLA-M-BEPR")
    STLA_M_EncapsulationClass.ExitPlantMode()
   
    Test, OBCFaultState = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('OBC_FAULT_STATE'),'OBC_FAULT_STATE', 0.0)
    Test, AcdcConversionState = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('ACDC_CONVERSION_STATE'),'ACDC_CONVERSION_STATE', 0.0)
    Test, IFB_V_VerInfo6or13or20 = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('IFB_V_VerInfo6or13or20'),'IFB_V_VerInfo6or13or20', 0.0)
    Test, IFB_Sample_Other_Resvd1 = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('IFB_Sample_Other_Resvd1'),'IFB_Sample_Other_Resvd1', 0.0)
    PreTestResult1 = OBCFaultState == 0
    PreTestResult2 = AcdcConversionState == 0
    PreTestResult3 = IFB_V_VerInfo6or13or20 == 0
    PreTestResult4 = IFB_Sample_Other_Resvd1 == 0
    PreCondition = True if PreTestResult1 and PreTestResult2 and PreTestResult3 and PreTestResult4 else False
    print(f"前置条件1结果:{PreTestResult1}, 前置条件2结果: {PreTestResult2}, 前置条件3结果: {PreTestResult3}, 前置条件4结果: {PreTestResult4}, 总结果: {PreCondition}")

    继电器控制板.Modbus.SetRegister(iID=1,Reg=3072,Data='8181')
    电阻控制板.Modbus.SetRegister(iID=1,Reg=3072,Data='220')
    STLA_CAN.DBC.SetSignal(1, get_message_for_signal('BMS_DC_RELAY_MES_EVSE_VOLTAGE'),'BMS_DC_RELAY_MES_EVSE_VOLTAGE', 20)
    信号发生器.SCPI.Write(':SOUR1:APPL:SQU 1000,12.1,0,0;:SOUR1:FUNC:SQU:DCYC 50;:OUTP1 ON')
    交流源载一体机.Set.Basic(ACPwrModeEnum.SOUR, ACChannelEnum.EACH, ACCouplingEnum.AC,0, ACPwrWorkModeEnum.CC)
    交流源载一体机.Set.Freq(dFreq=50)
    交流源载一体机.Set.Volt(dealListData([20.0, 20.0, 20.0]),dealListData([0.0, 0.0, 0.0]))
    交流源载一体机.Out.Enable(ACeEnable.ON)
    Sleep(17000)

    all_results = {}
    config_values = [4, 5, 6, 7]
    assignment_codes = [156, 157, 158, 159]
    result_names = [
        "Result_Test_ACPhaseOutOfRange",
        "Result_Test_ProxiVoltageOutOfRange",
        "Result_Test_PilotDutyOutOfRange",
        "Result_Test_DCLinesOutOfRange"
    ]
    
    for config in config_values:
        STLA_CAN.DBC.SetSignal(1, get_message_for_signal('CONFIG_VHL'), 'CONFIG_VHL', config)
        
        test_results = []
        for code in assignment_codes:
            test_results.append(not STLA_M_EncapsulationClass.CheckFaultIsInFaultList(code))
        
        combined_result = all(test_results)
        all_results[f"CONFIG_VHL_{config}"] = {
            'individual_results': dict(zip(result_names, test_results)),
            'combined_result': combined_result
        }
        
        print(f"\n=== CONFIG_VHL = {config} ===")
        for name, result in zip(result_names, test_results):
            print(f"{name} = {result}")
        print(f"Combined Result = {combined_result}")
        
    print("\n=== 最终汇总 ===")
    final_result = True
    for config, results in all_results.items():
        print(f"{config}:")
        for test_name, result in results['individual_results'].items():
            print(f"  {test_name}: {result}")
        print(f"  综合结果: {results['combined_result']}")

        if not results['combined_result']:
            final_result = False

    STLA_M_EncapsulationClass.Send590DiagMessageAndLog(
        message="02 3E 00",
        expected_response=["0x02", "0x7E", "0x00"],
        check_len=3
    )
    STLA_M_EncapsulationClass.Send590DiagMessageAndLog(
        message="03 22 D4 F7",
        expected_response=["0x04", "0x62", "0xD4", "0xF7", "0x00"],
        check_len=5
    )


    STLA_M_EncapsulationClass.ExitPlantMode()
    STLA_M_EncapsulationClass.TestCaseConfig(RecordStart = False, case_name = "STLA-M-BEPR")
    STLA_M_EncapsulationClass.RCD_Exit_EcoMode()
    STLA_M_EncapsulationClass.CloseAllDevice()
    STLA_M_EncapsulationClass.CloseAllCANMessage()
    TestResult1 = not(STLA_M_EncapsulationClass.PlantModeScreenshot(faultcode=assignment_codes[0], VerifyWhetherReportFault=False))


    print(f"前置条件结果:{PreCondition}, 测试步骤1结果: {TestResult1}, 测试步骤2结果: {final_result}")
    TestResult = True if PreCondition and TestResult1 and final_result else False
    if TestResult == True:
        TestResultDisplay = '合格'
        print(TestResultDisplay)
    else:
        TestResultDisplay = '不合格'
        print(TestResultDisplay)
    
    all_prints = stop_capture_prints()
    Log4NetWrapper.WriteToOutput_KeyInfo(TestResultDisplay, 
        f"\n"+
        f"1. OBC is not enter Plant Mode later, Send CONFIG_VHL= 100 : Client or 101 : APV or 110 : Show room or 111 : Invalid, no 156~159 fault trigger. \n"+
        f"\n"+
        f"========================================================================="+
        f"\n"+
        f"{all_prints}"
    )




