from CommonFunction.FunctionClass_V2 import *
from UtilityClass.UtilityClass01_DeviceConnectInit import *
from CommonFunction.Common00_Fuction import *
from CommonFunction.Common04_SoftwareCommonFunction import STLA_M_EncapsulationClass


if __name__ == '__main__':

    start_capture_prints()
    STLA_M_EncapsulationClass.InitDevice()
    STLA_M_EncapsulationClass.InitAllCANMessage()
    STLA_M_EncapsulationClass.TestCaseConfig(RecordStart = True, case_name = "STLA-M-VC2_TS_V2L")

    STLA_M_EncapsulationClass.V2LSignalPrecondition()
    STLA_CAN.DBC.SetSignal(1, get_message_for_signal('ACDC_CONVERSION_REQUEST'), 'ACDC_CONVERSION_REQUEST', 3)
    继电器控制板.Modbus.SetRegister(iID=1,Reg=3072,Data='8181')
    低压辅源.SCPI.Write(':SOUR1:VOLT 12.0;:SOUR1:CURR 3;:OUTP CH1,ON')
    电阻控制板.Modbus.SetRegister(iID=1,Reg=3072,Data='220')
    Sleep(8000)
    Test, MeasureKL30Current = 低压辅源.SCPI.Query(':MEAS:CURR? CH1')
    MeasureKL30Current = list(MeasureKL30Current)
    PreTestResult0 = MeasureKL30Current[0] <= 0.05
    print(MeasureKL30Current[0], PreTestResult0)

    信号发生器.SCPI.Write(':SOUR1:APPL:SQU 500,12,0,0;:SOUR1:FUNC:SQU:DCYC 53;:OUTP1 ON')
    Sleep(500)
    信号发生器.SCPI.Write(':SOUR1:APPL:SQU 500,12,0,0;:SOUR1:FUNC:SQU:DCYC 53;:OUTP1 OFF')
    Sleep(500)
    信号发生器.SCPI.Write(':SOUR1:APPL:SQU 500,12,0,0;:SOUR1:FUNC:SQU:DCYC 53;:OUTP1 ON')
    # 低压辅源.SCPI.Write(':SOUR3:VOLT 0.6;:SOUR3:CURR 3;:OUTP CH3,ON')
    # Sleep(5000)
    # Sleep(65000)

    高压源载一体机.Set.Basic(DCPwrModeEnum.NORM, DCPwrWorkModeEnum.NONE)
    高压源载一体机.Set.Volt(dVolt=350)
    高压源载一体机.Set.Curr(DCPwrSLEnum.SOUR, 20)
    高压源载一体机.Out.Enable(eEnable.ON)
    # STLA_M_EncapsulationClass.V2LCPVoltagePrecondition()
    # Sleep(1000)

    # Sleep(65000)
    # Sleep(500)
    # 信号发生器.SCPI.Write(':SOUR1:APPL:SQU 500,12,0,0;:SOUR1:FUNC:SQU:DCYC 53;:OUTP1 ON')
    # 信号发生器.SCPI.Write(':SOUR1:APPL:SQU 500,12,0,0;:SOUR1:FUNC:SQU:DCYC 53;:OUTP1 OFF')


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
    PreCondition = True if PreTestResult0 and PreTestResult1 and PreTestResult2 and PreTestResult3 and PreTestResult4 and PreTestResult5 else False
    print(f"KL30电流:{MeasureKL30Current[0]},前置条件0结果:{PreTestResult0}")
    print(f"OBC_FAULT_STATE:{OBCFaultState},前置条件1结果:{PreTestResult1}")
    print(f"AC_CHARGE_MODE_AVAIL:{ACChargeModeAvail},前置条件2结果:{PreTestResult2}")
    print(f"CCS_V2L_PLUG_DETECTED:{CCSV2LPlugDetected},前置条件3结果:{PreTestResult3}")
    print(f"BIDIR_V2L_AVAIL:{BidirV2LAvail},前置条件4结果:{PreTestResult4}")
    print(f"IFB_CCCP_CP_Volt:{CPVolt},前置条件5结果:{PreTestResult5}")

    Sleep(5000)
    Test, ACDCConversionState = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('ACDC_CONVERSION_STATE'),'ACDC_CONVERSION_STATE', 0.0)
    Test, OBCACVoltage = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('OBC_EVSE_MES_AC_VOLTAGE'),'OBC_EVSE_MES_AC_VOLTAGE', 0.0)
    TestResult11 = ACDCConversionState == 4
    Test, Measure_ACVoltage = 功率分析仪.Meas.Volt(PAVoltEnum.RMS, dealListData([0]*8))
    Measure_ACVoltage = list(Measure_ACVoltage)[0]
    TestResult12 = Measure_ACVoltage > 220
    TestResult13 = abs(Measure_ACVoltage - OBCACVoltage)/Measure_ACVoltage <= 0.03
    TestResult1 = True if TestResult11 and TestResult12 and TestResult13 else False
    print(f"ACDC_CONVERSION_STATE:{ACDCConversionState},测试结果1-1:{TestResult11}")
    print(f"OBC_EVSE_MES_AC_VOLTAGE:{OBCACVoltage},功率分析仪测量的交流电压:{Measure_ACVoltage},测试结果1-2:{TestResult12},测试结果1-3:{TestResult13}")

    Sleep(5000)
    STLA_M_EncapsulationClass.TestCaseConfig(RecordStart = False, case_name = "STLA-M-VC2_TS_V2L")
    STLA_M_EncapsulationClass.CloseAllCANMessage()
    STLA_M_EncapsulationClass.CloseAllDevice()

    Test, dArrTimeStamp1, dArrTimeStampList1 = STLA_CAN.DBC.FindValueOfSignal(get_message_for_signal('ACDC_CONVERSION_STATE'),'ACDC_CONVERSION_STATE',4,ConditionEnum.Equal,0,0)
    Test, dArrTimeStamp2, dArrTimeStampList2 = STLA_CAN.DBC.FindValueOfSignal(get_message_for_signal('OBC_EVSE_MES_AC_VOLTAGE'),'OBC_EVSE_MES_AC_VOLTAGE',220,ConditionEnum.Morethan,0,0)
    Time1 = dArrTimeStamp1[0]
    Time2 = dArrTimeStamp2[0]

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
        f"1.OBC start output voltage within 2s after wake request.\n"+
        f"\n"+
        f"========================================================================="+
        f"\n"+
        f"{all_prints}"
    )


