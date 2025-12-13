from CommonFunction.FunctionClass_V2 import *
from UtilityClass.UtilityClass01_DeviceConnectInit import *
from CommonFunction.Common00_Fuction import *
from CommonFunction.Common04_SoftwareCommonFunction import STLA_M_EncapsulationClass


if __name__ == '__main__':

    start_capture_prints()
    STLA_M_EncapsulationClass.InitDevice()
    STLA_M_EncapsulationClass.InitAllCANMessage()
    STLA_M_EncapsulationClass.TestCaseConfig(RecordStart = True, case_name = "STLA-M-VC2_TS_V2L")
    STLA_M_EncapsulationClass.V2LCPVoltagePrecondition()

    Time1 = TimeStamp()     # 获取毫秒级时间戳
    Test, OBCFaultState = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('OBC_FAULT_STATE'),'OBC_FAULT_STATE', 0.0)
    Test, ACChargeModeAvail = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('AC_CHARGE_MODE_AVAIL'),'AC_CHARGE_MODE_AVAIL', 0.0)
    Test, CCSV2LPlugDetected = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('CCS_V2L_PLUG_DETECTED'),'CCS_V2L_PLUG_DETECTED', 0.0)
    Test, BidirV2LAvail = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('BIDIR_V2L_AVAIL'),'BIDIR_V2L_AVAIL', 0.0)
    Test, CPVolt = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('IFB_CCCP_CP_Volt'),'IFB_CCCP_CP_Volt', 0.0)
    PreTestResult1 = OBCFaultState <= 0
    PreTestResult2 = ACChargeModeAvail == 0
    PreTestResult3 = CCSV2LPlugDetected == 1
    PreTestResult4 = BidirV2LAvail == 1
    PreTestResult5 = CPVolt >= 5.0
    PreCondition = True if PreTestResult1 and PreTestResult2 and PreTestResult3 and PreTestResult4 and PreTestResult5 else False
    print(f"OBC_FAULT_STATE:{OBCFaultState},前置条件1结果:{PreTestResult1}")
    print(f"AC_CHARGE_MODE_AVAIL:{ACChargeModeAvail},前置条件2结果:{PreTestResult2}")
    print(f"CCS_V2L_PLUG_DETECTED:{CCSV2LPlugDetected},前置条件3结果:{PreTestResult3}")
    print(f"BIDIR_V2L_AVAIL:{BidirV2LAvail},前置条件4结果:{PreTestResult4}")
    print(f"IFB_CCCP_CP_Volt:{CPVolt},前置条件5结果:{PreTestResult5}")

    STLA_M_EncapsulationClass.V2LSignalPrecondition()
    Test, EvsePlugLockState = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('EVSE_PLUG_LOCK_STATE'),'EVSE_PLUG_LOCK_STATE', 0.0)
    Test, OBCEvseState = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('OBC_EVSE_STATE'),'OBC_EVSE_STATE', 0.0)
    TestResult11 = EvsePlugLockState == 1
    TestResult12 = OBCEvseState == 5
    TestResult1 = True if TestResult11 and TestResult12 else False
    print(f"EVSE_PLUG_LOCK_STATE:{EvsePlugLockState},测试结果1-1:{TestResult11}")
    print(f"OBC_EVSE_STATE:{OBCEvseState},测试结果1-2:{TestResult12}")

    交流源载一体机.Set.Basic(ACPwrModeEnum.LOAD, ACChannelEnum.SING, ACCouplingEnum.AC,0, ACPwrWorkModeEnum.CC)
    交流源载一体机.Set.Curr(dealListData([5.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
                     dealListData([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]))
    交流源载一体机.Out.Enable(ACeEnable.ON)
    Sleep(1000)

    STLA_CAN.DBC.SetSignal(1, get_message_for_signal('ACDC_CONVERSION_REQUEST'), 'ACDC_CONVERSION_REQUEST', 3)
    Sleep(5000)
    Test, ACDCConversionState = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('ACDC_CONVERSION_STATE'),'ACDC_CONVERSION_STATE', 0.0)
    Test, OBCACVoltage = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('OBC_EVSE_MES_AC_VOLTAGE'),'OBC_EVSE_MES_AC_VOLTAGE', 0.0)
    TestResult21 = ACDCConversionState == 4
    Test, Measure_ACVoltage = 功率分析仪.Meas.Volt(PAVoltEnum.RMS, dealListData([0]*8))
    Measure_ACVoltage = list(Measure_ACVoltage)[0]
    TestResult22 = Measure_ACVoltage > 220
    TestResult23 = abs(Measure_ACVoltage - OBCACVoltage)/Measure_ACVoltage <= 0.03

    交流源载一体机.Set.Curr(dealListData([10.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
                     dealListData([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]))
    Sleep(5000)
    Test, Measure_ACCurrent = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('P_IacRpt_IacRms_A'),'P_IacRpt_IacRms_A', 0.0)
    TestResult24 = abs(Measure_ACCurrent - 10) <= 1
    TestResult2 = True if TestResult21 and TestResult22 and TestResult23 and TestResult24 else False
    print(f"ACDC_CONVERSION_STATE:{ACDCConversionState},测试结果2-1:{TestResult21}")
    print(f"OBC_EVSE_MES_AC_VOLTAGE:{OBCACVoltage},功率分析仪测量的交流电压:{Measure_ACVoltage},测试结果2-2:{TestResult22},测试结果2-3:{TestResult23}")
    print(f"功率分析仪测量的交流电流:{Measure_ACCurrent},测试结果2-4:{TestResult24}")

    Sleep(5000)
    STLA_M_EncapsulationClass.TestCaseConfig(RecordStart = False, case_name = "STLA-M-VC2_TS_V2L")
    STLA_M_EncapsulationClass.CloseAllCANMessage()
    STLA_M_EncapsulationClass.CloseAllDevice()

    Test, dArrTimeStamp1, dArrTimeStampList1 = STLA_CAN.DBC.FindValueOfSignal(get_message_for_signal('P_IacRpt_IacRms_A'),'P_IacRpt_IacRms_A',5,ConditionEnum.Morethan,0,0)
    Test, dArrTimeStamp2, dArrTimeStampList2 = STLA_CAN.DBC.FindValueOfSignal(get_message_for_signal('P_IacRpt_IacRms_A'),'P_IacRpt_IacRms_A',10,ConditionEnum.Morethan,0,0)
    Time1 = dArrTimeStamp1[5]
    Time2 = dArrTimeStamp2[5]

    CursorPosition = replace_zeros([Time1, Time2])
    signal_list = ['IFB_V_VerInfo6or13or20','IFB_Volt_KL30','IFB_Volt_KL15','RCD_LINE_STATE',
                   'IFB_CCCP_CC_Res','IFB_CCCP_CP_Volt','OBC_FAULT_STATE','DCDC_FAULT_STATE','OBC_EVSE_MES_AC_VOLTAGE',
                   'AC_CHARGE_MODE_AVAIL','CCS_V2L_PLUG_DETECTED','BIDIR_V2L_AVAIL','ACDC_CONVERSION_REQUEST','ACDC_CONVERSION_STATE',
                   'P_VacRpt_VacRms_A','P_IacRpt_IacRms_A','OBC_DC_AC_ACTIV_POWER']
    message_list = get_messages_for_signals(signal_list)
    STLA_CAN.DBC.ExportWfmFile(message_list,signal_list,'')
    Sleep(2000)
    STLA_CAN.DBC.ConfigureCursor(CursorEnum.X,CursorPosition)
    STLA_CAN.DBC.ExportImage(ImageFormatEnum.PNG,ColorInversionEnum.ON,'')

    print(f"前置条件结果: {PreCondition}, 测试步骤1结果: {TestResult1}, 测试步骤2结果: {TestResult2}")
    TestResult = True if PreCondition and TestResult1 and TestResult2 else False
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
        f"1.EVSE_PLUG_LOCK_STATE={EvsePlugLockState}.\n"+
        f"2.OBC_EVSE_STATE={OBCEvseState}.\n"+
        f"3.ACDC_CONVERSION_STATE={ACDCConversionState},Machine starting,the output power is generated.\n"+
        f"\n"+
        f"========================================================================="+
        f"\n"+
        f"{all_prints}"
    )





