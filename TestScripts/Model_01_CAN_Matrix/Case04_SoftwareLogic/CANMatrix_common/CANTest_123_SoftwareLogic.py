from CommonFunction.FunctionClass_V2 import *
from UtilityClass.UtilityClass01_DeviceConnectInit import *
from CommonFunction.Common00_Fuction import *
from CommonFunction.Common04_SoftwareCommonFunction import STLA_M_EncapsulationClass

if __name__ == '__main__':

    start_capture_prints()
    STLA_M_EncapsulationClass.InitDevice()
    STLA_M_EncapsulationClass.InitAllCANMessage()
    STLA_M_EncapsulationClass.TestCaseConfig(RecordStart = True, case_name="STLA-M-Common_SoftwareLogic")
    PreCondition = STLA_M_EncapsulationClass.LowVoltageSleepAndWakeup()

    Test, ACDCConversionState = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('ACDC_CONVERSION_STATE'),'ACDC_CONVERSION_STATE', 0.0)
    Test, DCDCStateBB = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('DCDC_STATE_BB'),'DCDC_STATE_BB', 0.0)
    TestResult11 = ACDCConversionState == 0
    TestResult12 = DCDCStateBB == 2
    TestResult1 = True if TestResult11 and TestResult12 else False
    print(f"ACDCConversionState == {ACDCConversionState}, 测试步骤11结果: {TestResult11}")
    print(f"DCDCStateBB == {DCDCStateBB}, 测试步骤12结果: {TestResult12}")

    TestResult2 = STLA_M_EncapsulationClass.OBCState_Charge(OBC_ReqMode=1, OBC_State=2)
    Test, OBCDCMaxPower1 = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('OBC_DC_MAX_POWER'),'OBC_DC_MAX_POWER', 0.0)
    TestResult31 = abs(abs(OBCDCMaxPower1) - 10600 ) <= 600

    STLA_CAN.DBC.Trigger(1,'DAT_E_VCU_4F1',False)
    Sleep(2000)
    Test, OBCDCMaxPower2 = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('OBC_DC_MAX_POWER'),'OBC_DC_MAX_POWER', 0.0)
    Test, ACDCConversionState = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('ACDC_CONVERSION_STATE'),'ACDC_CONVERSION_STATE', 0.0)
    TestResult32 = OBCDCMaxPower2 == 0
    TestResult33 = ACDCConversionState == 0
    TestResult3 = True if TestResult31 and TestResult32 and TestResult33 else False
    print(f"OBC_DC_MAX_POWER == {OBCDCMaxPower1}, 测试步骤31结果: {TestResult31}")
    print(f"OBC_DC_MAX_POWER == {OBCDCMaxPower2}, 测试步骤32结果: {TestResult32}")
    print(f"ACDC_CONVERSION_STATE == {ACDCConversionState}, 测试步骤33结果: {TestResult33}")

    STLA_M_EncapsulationClass.TestCaseConfig(RecordStart = False, case_name="STLA-M-Common_SoftwareLogic")
    STLA_M_EncapsulationClass.CloseAllCANMessage()
    STLA_M_EncapsulationClass.CloseAllDevice()

    Test1, dArrTimeStamp1, dArrTimeStampList1 = STLA_CAN.DBC.FindValueOfSignal(get_message_for_signal('ACDC_CONVERSION_STATE'),'ACDC_CONVERSION_STATE',2,ConditionEnum.Equal,0,0)
    Time1 = dArrTimeStamp1[0]
    Test2, dArrTimeStamp2, dArrTimeStampList2 = STLA_CAN.DBC.FindValueOfSignal(get_message_for_signal('ACDC_CONVERSION_STATE'),'ACDC_CONVERSION_STATE',2,ConditionEnum.Unequal,Time1,0)
    Time2 = dArrTimeStamp2[0]

    CursorPosition = replace_zeros([Time1, Time2])
    signal_list = ['IFB_V_VerInfo6or13or20','IFB_Volt_KL30','IFB_Volt_KL15','IFB_Volt_LVCC','RCD_LINE_STATE',
                   'IFB_CCCP_CC_Res','IFB_CCCP_CP_Volt','IFB_CCCP_CP_Fre','IFB_CCCP_CP_Duty',
                   'ECU_ELEC_STATE_RCD','DCDC_STATE_BB','ACDC_CONVERSION_REQUEST','ACDC_CONVERSION_STATE','MAX_INDI_CHRG_CURR','OBC_DC_MAX_POWER',
                   'DCDC_FAULT_STATE','OBC_FAULT_STATE']
    STLA_CAN.DBC.ExportWfmFile(get_messages_for_signals(signal_list),signal_list,'')
    Sleep(2000)
    STLA_CAN.DBC.ConfigureCursor(CursorEnum.X,CursorPosition)
    STLA_CAN.DBC.ExportImage(ImageFormatEnum.PNG,ColorInversionEnum.ON,'')

    print(f"前置条件结果:{PreCondition}, 测试步骤1结果: {TestResult1}, 测试步骤2结果: {TestResult2}, 测试步骤3结果: {TestResult3}")
    TestResult = True if PreCondition and TestResult1 and TestResult2 and TestResult3 else False
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
        f"2. OBC enters Charge mode, reporting OBC_DC_MAX_POWER={OBCDCMaxPower1}Kw.\n"+
        f"3. The OBC enters Fault mode, reporting OBC_DC_MAX_POWER={OBCDCMaxPower2}W.\n"+
        f"\n"+
        f"========================================================================="+
        f"\n"+
        f"{all_prints}"
    )


