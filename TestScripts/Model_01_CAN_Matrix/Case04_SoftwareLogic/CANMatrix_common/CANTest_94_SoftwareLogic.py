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
    Test, DCDCFaultState1 = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('DCDC_FAULT_STATE'),'DCDC_FAULT_STATE', 0.0)
    TestResult11 = ACDCConversionState == 0
    TestResult12 = DCDCStateBB == 2
    TestResult13 = DCDCFaultState1 == 0
    TestResult1 = True if TestResult11 and TestResult12 and TestResult13 else False
    print(f"ACDCConversionState == {ACDCConversionState}, 测试步骤11结果: {TestResult11}")
    print(f"DCDCStateBB == {DCDCStateBB}, 测试步骤12结果: {TestResult12}")
    print(f"DCDCFaultState == {DCDCFaultState1}, 测试步骤13结果: {TestResult13}")

    TestResult2 = STLA_M_EncapsulationClass.DCDCState_Buck(DCDC_Mode=1,DCDC_State=3)
    
    高压源载一体机.Set.Volt(dVolt=475)
    Sleep(1000)
    Test, DCDCFaultState2 = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('DCDC_FAULT_STATE'),'DCDC_FAULT_STATE', 0.0)
    TestResult3 = DCDCFaultState2 == 1
    print(f"DCDCFaultState == {DCDCFaultState2}, 测试步骤3结果: {TestResult3}")

    STLA_CAN.DBC.SetSignal(1, get_message_for_signal('HV_ACTIVE_DISCH_REQ'), 'HV_ACTIVE_DISCH_REQ', 1)  
    高压源载一体机.Set.Volt(dVolt=365)
    Sleep(1000)
    高压源载一体机.Set.Volt(dVolt=290)
    Sleep(6000)
    Test, DCDCFaultState3 = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('DCDC_FAULT_STATE'),'DCDC_FAULT_STATE', 0.0)
    TestResult4 = DCDCFaultState3 == 2
    print(f"DCDCFaultState == {DCDCFaultState3}, 测试步骤4结果: {TestResult4}")

    STLA_CAN.DBC.SetSignal(1, get_message_for_signal('HV_ACTIVE_DISCH_REQ'), 'HV_ACTIVE_DISCH_REQ', 0)  
    高压源载一体机.Set.Volt(dVolt=365)

    STLA_M_EncapsulationClass.CloseAllDevice()
    STLA_M_EncapsulationClass.CloseAllCANMessage()
    STLA_M_EncapsulationClass.InitAllCANMessage()
    STLA_M_EncapsulationClass.LowVoltageSleepAndWakeup()
    STLA_CAN.DBC.Trigger(1,'DYN_E_VCU_428',False)
    Sleep(2000)
    Test, DCDCFaultState4 = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('DCDC_FAULT_STATE'),'DCDC_FAULT_STATE', 0.0)
    TestResult5 = DCDCFaultState4 == 3
    print(f"DCDCFaultState == {DCDCFaultState4}, 测试步骤5结果: {TestResult5}")

    STLA_M_EncapsulationClass.TestCaseConfig(RecordStart = False, case_name="STLA-M-Common_SoftwareLogic")
    STLA_M_EncapsulationClass.CloseAllCANMessage()
    STLA_M_EncapsulationClass.CloseAllDevice()

    Test1, dArrTimeStamp1, dArrTimeStampList1 = STLA_CAN.DBC.FindValueOfSignal(get_message_for_signal('DCDC_FAULT_STATE'),'DCDC_FAULT_STATE',0,ConditionEnum.Equal,0,0)
    Test2, dArrTimeStamp2, dArrTimeStampList2 = STLA_CAN.DBC.FindValueOfSignal(get_message_for_signal('DCDC_FAULT_STATE'),'DCDC_FAULT_STATE',1,ConditionEnum.Equal,0,0)
    Test3, dArrTimeStamp3, dArrTimeStampList3 = STLA_CAN.DBC.FindValueOfSignal(get_message_for_signal('DCDC_FAULT_STATE'),'DCDC_FAULT_STATE',2,ConditionEnum.Equal,0,0)
    Test4, dArrTimeStamp4, dArrTimeStampList4 = STLA_CAN.DBC.FindValueOfSignal(get_message_for_signal('DCDC_FAULT_STATE'),'DCDC_FAULT_STATE',3,ConditionEnum.Equal,0,0)
    Time1 = dArrTimeStamp1[0]
    Time2 = dArrTimeStamp2[0]
    Time3 = dArrTimeStamp3[0]
    Time4 = dArrTimeStamp4[0]

    CursorPosition = replace_zeros([Time1, Time2, Time3, Time4])
    signal_list = ['IFB_V_VerInfo6or13or20','IFB_Volt_KL30','IFB_Volt_KL15','IFB_Volt_LVCC','RCD_LINE_STATE',
                   'IFB_CCCP_CC_Res','IFB_CCCP_CP_Volt','IFB_CCCP_CP_Fre','IFB_CCCP_CP_Duty',
                   'ECU_ELEC_STATE_RCD','DCDC_STATE_BB','ACDC_CONVERSION_REQUEST','ACDC_CONVERSION_STATE','CURR_SETPOINT_DCDC_LV_REQ',
                   'DCDC_FAULT_STATE','OBC_FAULT_STATE']
    STLA_CAN.DBC.ExportWfmFile(get_messages_for_signals(signal_list),signal_list,'')
    Sleep(2000)
    STLA_CAN.DBC.ConfigureCursor(CursorEnum.X,CursorPosition)
    STLA_CAN.DBC.ExportImage(ImageFormatEnum.PNG,ColorInversionEnum.ON,'')

    print(f"前置条件结果:{PreCondition}, 测试步骤1结果: {TestResult1}, 测试步骤2结果: {TestResult2}, 测试步骤3结果: {TestResult3}, 测试步骤4结果: {TestResult4}, 测试步骤5结果: {TestResult5}")
    TestResult = True if PreCondition and TestResult1 and TestResult2 and TestResult3 and TestResult4 and TestResult5 else False
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
        f"2. DCDC_FAULT_STATE={DCDCFaultState1}.\n"+
        f"3. Reporting DCDC_FAULT_STATE = {DCDCFaultState2}.\n"+
        f"4. Reporting DCDC_FAULT_STATE = {DCDCFaultState3}.\n"+
        f"5. Reporting DCDC_FAULT_STATE = {DCDCFaultState4}.\n"+
        f"\n"+
        f"========================================================================="+
        f"\n"+
        f"{all_prints}"
    )






