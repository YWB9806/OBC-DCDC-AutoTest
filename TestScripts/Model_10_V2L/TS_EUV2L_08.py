from CommonFunction.FunctionClass_V2 import *
from UtilityClass.UtilityClass01_DeviceConnectInit import *
from CommonFunction.Common00_Fuction import *
from CommonFunction.Common04_SoftwareCommonFunction import STLA_M_EncapsulationClass


if __name__ == '__main__':

    start_capture_prints()
    STLA_M_EncapsulationClass.InitDevice()
    STLA_M_EncapsulationClass.InitAllCANMessage()
    STLA_M_EncapsulationClass.TestCaseConfig(RecordStart = True, case_name = "STLA-M-VC2_TS_V2L")

    继电器控制板.Modbus.SetRegister(iID=1,Reg=3072,Data='8180')
    # 低压辅源.SCPI.Write(':SOUR1:VOLT 6.0;:SOUR1:CURR 3;:OUTP CH1,ON')
    低压辅源.SCPI.Write(':SOUR1:VOLT 8.0;:SOUR1:CURR 3;:OUTP CH1,ON')
    低压辅源.SCPI.Write(':SOUR2:VOLT 5;:SOUR2:CURR 3;:OUTP CH2,ON')
    低压辅源.SCPI.Write(':SOUR3:VOLT 0.6;:SOUR3:CURR 3;:OUTP CH3,ON')
    电阻控制板.Modbus.SetRegister(iID=1,Reg=3072,Data='220')
    Sleep(130000)
    Test, OBCFaultState = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('OBC_FAULT_STATE'),'OBC_FAULT_STATE', 0.0)
    Test, ACChargeModeAvail = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('AC_CHARGE_MODE_AVAIL'),'AC_CHARGE_MODE_AVAIL', 0.0)
    Test, CCSV2LPlugDetected = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('CCS_V2L_PLUG_DETECTED'),'CCS_V2L_PLUG_DETECTED', 0.0)
    Test, BidirV2LAvail = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('BIDIR_V2L_AVAIL'),'BIDIR_V2L_AVAIL', 0.0)
    PreTestResult1 = OBCFaultState > 1
    PreTestResult2 = ACChargeModeAvail == 0
    PreTestResult3 = CCSV2LPlugDetected == 0
    PreTestResult4 = BidirV2LAvail == 0
    PreCondition = True if PreTestResult1 and PreTestResult2 and PreTestResult3 and PreTestResult4 else False
    print(f"OBC_FAULT_STATE:{OBCFaultState},前置条件1结果:{PreTestResult1}")
    print(f"AC_CHARGE_MODE_AVAIL:{ACChargeModeAvail},前置条件2结果:{PreTestResult2}")
    print(f"CCS_V2L_PLUG_DETECTED:{CCSV2LPlugDetected},前置条件3结果:{PreTestResult3}")
    print(f"BIDIR_V2L_AVAIL:{BidirV2LAvail},前置条件4结果:{PreTestResult4}")

    电阻控制板.Modbus.SetRegister(iID=1,Reg=3072,Data='1100')
    Sleep(1500)
    电阻控制板.Modbus.SetRegister(iID=1,Reg=3072,Data='20')
    Sleep(1500)
    电阻控制板.Modbus.SetRegister(iID=1,Reg=3072,Data='680')
    Sleep(1500)
    Test, CPVolt1 = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('IFB_CCCP_CP_Volt'),'IFB_CCCP_CP_Volt', 0.0)
    Test, CCSV2LPlugDetected1 = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('CCS_V2L_PLUG_DETECTED'),'CCS_V2L_PLUG_DETECTED', 0.0)
    TestResult11 = CPVolt1 >= 5.0
    TestResult12 = CCSV2LPlugDetected1 == 1
    TestResult1 = True if TestResult11 and TestResult12 else False
    print(f"IFB_CCCP_CP_Volt:{CPVolt1},测试结果1-1:{TestResult11}")
    print(f"CCS_V2L_PLUG_DETECTED:{CCSV2LPlugDetected1},测试结果1-2:{TestResult12}")

    电阻控制板.Modbus.SetRegister(iID=1,Reg=3072,Data='20')
    Sleep(1500)
    Test, BidirV2LAvail2 = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('BIDIR_V2L_AVAIL'),'BIDIR_V2L_AVAIL', 0.0)
    Test, CPVolt2 = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('IFB_CCCP_CP_Volt'),'IFB_CCCP_CP_Volt', 0.0)
    TestResult21 = BidirV2LAvail2 == 0
    TestResult22 = CPVolt2 == 0
    TestResult2 = True if TestResult21 and TestResult22 else False
    print(f"BIDIR_V2L_AVAIL:{BidirV2LAvail2},测试结果2-1:{TestResult21}")
    print(f"IFB_CCCP_CP_Volt:{CPVolt2},测试结果2-2:{TestResult22}")
   
    Sleep(5000)
    STLA_M_EncapsulationClass.TestCaseConfig(RecordStart = False, case_name = "STLA-M-VC2_TS_V2L")
    STLA_M_EncapsulationClass.CloseAllCANMessage()
    STLA_M_EncapsulationClass.CloseAllDevice()

    Test, dArrTimeStamp1, dArrTimeStampList1 = STLA_CAN.DBC.FindValueOfSignal(get_message_for_signal('CCS_V2L_PLUG_DETECTED'),'CCS_V2L_PLUG_DETECTED',0,ConditionEnum.Equal,0,0)
    Test, dArrTimeStamp2, dArrTimeStampList2 = STLA_CAN.DBC.FindValueOfSignal(get_message_for_signal('IFB_CCCP_CP_Volt'),'IFB_CCCP_CP_Volt',5,ConditionEnum.Morethan,0,0)
    Test, dArrTimeStamp3, dArrTimeStampList3 = STLA_CAN.DBC.FindValueOfSignal(get_message_for_signal('BIDIR_V2L_AVAIL'),'BIDIR_V2L_AVAIL',1,ConditionEnum.Equal,0,0)
    Time1 = dArrTimeStamp1[5]
    Time2 = dArrTimeStamp2[0]
    Time3 = dArrTimeStamp3[0]
    Test, dArrTimeStamp4, dArrTimeStampList4 = STLA_CAN.DBC.FindValueOfSignal(get_message_for_signal('IFB_CCCP_CP_Volt'),'IFB_CCCP_CP_Volt',0,ConditionEnum.Equal,Time3,0)
    Time4 = dArrTimeStamp4[0]

    CursorPosition = replace_zeros([Time1, Time2, Time3, Time4])
    signal_list = ['IFB_V_VerInfo6or13or20','IFB_Volt_KL30','IFB_Volt_KL15','RCD_LINE_STATE',
                   'IFB_CCCP_CC_Res','IFB_CCCP_CP_Volt','OBC_FAULT_STATE','DCDC_FAULT_STATE','OBC_EVSE_MES_AC_VOLTAGE',
                   'AC_CHARGE_MODE_AVAIL','CCS_V2L_PLUG_DETECTED','BIDIR_V2L_AVAIL']
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
        f"1.CP voltage ={CPVolt1}V,CCS_V2L_PLUG_DETECTED=1 : Detected.\n"+
        f"2.CP voltage ={CPVolt2}V,BIDIR_V2L_AVAIL={BidirV2LAvail2}.\n"+
        f"\n"+
        f"========================================================================="+
        f"\n"+
        f"{all_prints}"
    )







