from CommonFunction.FunctionClass_V2 import *
from UtilityClass.UtilityClass01_DeviceConnectInit import *
from CommonFunction.Common00_Fuction import *
from CommonFunction.Common04_SoftwareCommonFunction import STLA_M_EncapsulationClass

if __name__ == '__main__':

    start_capture_prints()
    STLA_M_EncapsulationClass.InitDevice()
    STLA_M_EncapsulationClass.InitAllCANMessage()
    STLA_M_EncapsulationClass.TestCaseConfig(RecordStart = True, case_name="STLA-M-Common_ForbiddenValue")
    PreCondition = STLA_M_EncapsulationClass.LowVoltageSleepAndWakeup()

    Test, ACDCConversionState = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('ACDC_CONVERSION_STATE'),'ACDC_CONVERSION_STATE', 0.0)
    Test, DCDCStateBB = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('DCDC_STATE_BB'),'DCDC_STATE_BB', 0.0)
    TestResult11 = ACDCConversionState == 0
    TestResult12 = DCDCStateBB == 2
    TestResult1 = True if TestResult11 and TestResult12 else False
    print(f"ACDCConversionState == 0, 测试步骤11结果: {TestResult11}")
    print(f"DCDCStateBB == 2, 测试步骤12结果: {TestResult12}")

    _ , TestResult2 = STLA_M_EncapsulationClass.CANMatrixForbiddenValueTest('RESET_ANTICIPE', forbidden_values=[5, 10, 15], normal_value=0, fault_code=127)
    STLA_M_EncapsulationClass.TestCaseConfig(RecordStart = False, case_name="STLA-M-Common_ForbiddenValue")
    STLA_M_EncapsulationClass.CloseAllCANMessage()
    STLA_M_EncapsulationClass.CloseAllDevice()

    Test1, dArrTimeStamp1, dArrTimeStampList1 = STLA_CAN.DBC.FindValueOfSignal(get_message_for_signal('RESET_ANTICIPE'),'RESET_ANTICIPE',5,ConditionEnum.Equal,0,0)
    StartTime1 = dArrTimeStamp1[0]
    Test2, dArrTimeStamp2, dArrTimeStampList2 = STLA_CAN.DBC.FindValueOfSignal(get_message_for_signal('IFB_V_VerInfo6or13or20'),'IFB_V_VerInfo6or13or20',127,ConditionEnum.Equal,StartTime1,0)
    EndTime1 = dArrTimeStamp2[0]
    Test3, dArrTimeStamp3, dArrTimeStampList3 = STLA_CAN.DBC.FindValueOfSignal(get_message_for_signal('RESET_ANTICIPE'),'RESET_ANTICIPE',15,ConditionEnum.Equal,0,0)
    StartTime2 = dArrTimeStamp3[0]
    Test4, dArrTimeStamp4, dArrTimeStampList4 = STLA_CAN.DBC.FindValueOfSignal(get_message_for_signal('IFB_V_VerInfo6or13or20'),'IFB_V_VerInfo6or13or20',127,ConditionEnum.Equal,StartTime2,0)
    EndTime2 = dArrTimeStamp4[0]

    CursorPosition = replace_zeros([StartTime1, EndTime1, StartTime2, EndTime2])
    signal_list = ['IFB_V_VerInfo6or13or20','IFB_Volt_KL30','IFB_Volt_KL15','IFB_Volt_LVCC','RCD_LINE_STATE','DCDC_FAULT_STATE','OBC_FAULT_STATE',
                   'IFB_CCCP_CC_Res','IFB_CCCP_CP_Volt','IFB_CCCP_CP_Fre','IFB_CCCP_CP_Duty',
                   'ECU_ELEC_STATE_RCD','DCDC_STATE_BB','ACDC_CONVERSION_REQUEST','ACDC_CONVERSION_STATE','RESET_ANTICIPE'
                   ]
    STLA_CAN.DBC.ExportWfmFile(get_messages_for_signals(signal_list),signal_list,'')
    Sleep(2000)
    STLA_CAN.DBC.ConfigureCursor(CursorEnum.X,CursorPosition)
    STLA_CAN.DBC.ExportImage(ImageFormatEnum.PNG,ColorInversionEnum.ON,'')

    print(f"前置条件结果:{PreCondition}, 测试步骤1结果: {TestResult1}, 测试步骤2结果: {TestResult2}")
    TestResult = True if PreCondition and TestResult1 and TestResult2 else False
    if TestResult == True:
        TestResultDisplay = '合格'
        print(TestResultDisplay)
    else:
        TestResultDisplay = '不合格'
        print(TestResultDisplay)
    
    all_prints = stop_capture_prints()
    Log4NetWrapper.WriteToOutput_KeyInfo(TestResultDisplay, 
        f"\n"+
        f"1. After the OBC wakes up, check the signa period, initial value, and view signa l_ength, Byte_Position and Bit_Position in DBC.\n"+
        f"2. /.\n"+
        f"3. Triggering a Level 2 failure, and reporting IFB_V_VerInfo6or13or20=127, there is no the replacemennt value.\n"+
        f"\n"+
        f"========================================================================="+
        f"\n"+
        f"{all_prints}"
    )



