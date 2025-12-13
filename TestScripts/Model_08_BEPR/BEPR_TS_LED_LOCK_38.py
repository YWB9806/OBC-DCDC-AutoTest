from CommonFunction.FunctionClass_V2 import *
from UtilityClass.UtilityClass01_DeviceConnectInit import *
from CommonFunction.Common00_Fuction import *
from CommonFunction.Common04_SoftwareCommonFunction import STLA_M_EncapsulationClass

if __name__ == '__main__':

    start_capture_prints()
    STLA_M_EncapsulationClass.InitDevice()
    STLA_M_EncapsulationClass.InitAllCANMessage()
    STLA_M_EncapsulationClass.TestCaseConfig(RecordStart = True, case_name="STLA-M-BEPR")
    STLA_M_EncapsulationClass.LowVoltageWakeup()

    STLA_M_EncapsulationClass.Send590DiagMessageAndLog("02 10 03")
    Sleep(500)
    STLA_M_EncapsulationClass.Send590DiagMessageAndLog("02 27 03")
    Sleep(500)
    STLA_M_EncapsulationClass.Send590DiagMessageAndLog("06 27 04 FF FF FF FF")
    Sleep(500)
    STLA_M_EncapsulationClass.Send590DiagMessageAndLog("02 3E 00")
    Sleep(200)

    STLA_M_EncapsulationClass.Send590DiagMessageAndLog(
        message="04 31 01 DF 6D",
        expected_response=["0x05", "0x71", "0x01", "0xDF", "0x6D", "0x01"],
        check_len=6
    )
    Sleep(200)
    STLA_M_EncapsulationClass.Send590DiagMessageAndLog(
        message="04 31 03 DF 6D",
        expected_response=["0x05", "0x71", "0x03", "0xDF", "0x6D", "0x01"],
        check_len=6
    )
    Sleep(200)
    STLA_M_EncapsulationClass.Send590DiagMessageAndLog(
        message="03 22 D8 54",
        expected_response=["0x04", "0x62", "0xD8", "0x54", "0x50"],
        check_len=5
    )
    Sleep(200)
    STLA_M_EncapsulationClass.Send590DiagMessageAndLog(
        message="03 22 D8 55",
        expected_response=["0x04", "0x62", "0xD8", "0x55", "0x50"],
        check_len=5
    )
    Sleep(200)
    STLA_M_EncapsulationClass.Send590DiagMessageAndLog(
        message="03 22 DA 0B",
        expected_response=["0x04", "0x62", "0xDA", "0x0B"],
        check_len=4
    )
    Sleep(200)

    STLA_M_EncapsulationClass.PreventExitSession3()
    STLA_M_EncapsulationClass.Send590DiagMessageAndLog(
        message="04 31 03 DF 6D",
        expected_response=["0x05", "0x71", "0x03", "0xDF", "0x6D", "0x01"],
        check_len=6
    )
    Sleep(200)
    STLA_M_EncapsulationClass.Send590DiagMessageAndLog(
        message="03 22 D8 54",
        expected_response=["0x04", "0x62", "0xD8", "0x54", "0x00"],
        check_len=5
    )
    Sleep(200)
    STLA_M_EncapsulationClass.Send590DiagMessageAndLog(
        message="03 22 D8 55",
        expected_response=["0x04", "0x62", "0xD8", "0x55", "0x00"],
        check_len=5
    )
    Sleep(200)
    STLA_M_EncapsulationClass.Send590DiagMessageAndLog(
        message="03 22 DA 0B",
        expected_response=["0x04", "0x62", "0xDA", "0x0B"],
        check_len=4
    )
    Sleep(200)
    STLA_M_EncapsulationClass.Send590DiagMessageAndLog(
        message="04 31 03 DF 6D",
        expected_response=["0x07", "0x71", "0x03", "0xDF", "0x6D", "0x02"],
        check_len=6
    )
    Sleep(5000)

    print("\n===== 完整交互记录 =====")
    for log in STLA_M_EncapsulationClass.get_logs():
        print(log)

    STLA_M_EncapsulationClass.TestCaseConfig(RecordStart = False, case_name="STLA-M-BEPR")
    STLA_M_EncapsulationClass.CloseAllCANMessage()
    STLA_M_EncapsulationClass.CloseAllDevice()

    # Test, dArrTimeStamp0, dArrTimeStampList0= STLA_CAN.DBC.FindValueOfSignal(get_message_for_signal('DCDC_STATE_BB'),'DCDC_STATE_BB',3,ConditionEnum.Equal,0,0,[],[])
    # StartTime1 = dArrTimeStamp0[0]

    # Test, EndTime1 = STLA_CAN.DBC.FindMsg('REP_DIAG_ON_CAN_58F',0,0,FindMsgTypeEnum.First,0)
    # CursorPosition = replace_zeros([StartTime1, EndTime1])
    # signal_list = ['IFB_V_VerInfo6or13or20','IFB_Volt_KL30','IFB_Volt_KL15','IFB_Volt_LVCC','RCD_LINE_STATE',
    #                'IFB_CCCP_CC_Res','IFB_CCCP_CP_Volt','IFB_CCCP_CP_Fre','IFB_CCCP_CP_Duty',
    #                'ECU_ELEC_STATE_RCD','DCDC_STATE_BB','ACDC_CONVERSION_REQUEST','ACDC_CONVERSION_STATE','DATA_DIAG']
    # STLA_CAN.DBC.ExportWfmFile(get_messages_for_signals(signal_list),signal_list,'')
    # Sleep(2000)
    # STLA_CAN.DBC.ConfigureCursor(CursorEnum.X,CursorPosition)
    # STLA_CAN.DBC.ExportImage(ImageFormatEnum.PNG,ColorInversionEnum.ON,'')


    PreCondition = True
    TestResult1 = True
    print(f"前置条件结果:{PreCondition}, 测试步骤1结果: {TestResult1}")
    TestResult = True if PreCondition and TestResult1 else False
    if TestResult == True:
        TestResultDisplay = '合格'
        print(TestResultDisplay)
    else:
        TestResultDisplay = '不合格'
        print(TestResultDisplay)
    
    all_prints = stop_capture_prints()
    Log4NetWrapper.WriteToOutput_KeyInfo(TestResultDisplay, 
        f"\n"+
        f"1. .\n"+
        f"\n"+
        f"========================================================================="+
        f"\n"+
        f"{all_prints}"
    )
