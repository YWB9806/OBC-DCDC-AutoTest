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
    STLA_CAN.DBC.SetSignal(1, get_message_for_signal('REVEIL_PRINCIPAL'), 'REVEIL_PRINCIPAL', 1)  
    Sleep(1000)
    Test, ECUElecStateRCD = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('ECU_ELEC_STATE_RCD'),'ECU_ELEC_STATE_RCD', 0.0)
    TestResult1 = ECUElecStateRCD == 2
    print(f"ECU_ELEC_STATE_RCD == {ECUElecStateRCD}, 测试步骤1结果: {TestResult1}")
    Sleep(5000)
    STLA_M_EncapsulationClass.TestCaseConfig(RecordStart = False, case_name="STLA-M-Common_SoftwareLogic")
    STLA_M_EncapsulationClass.CloseAllCANMessage()
    STLA_M_EncapsulationClass.CloseAllDevice()

    Test1, dArrTimeStamp1, dArrTimeStampList1 = STLA_CAN.DBC.FindValueOfSignal(get_message_for_signal('ECU_ELEC_STATE_RCD'),'ECU_ELEC_STATE_RCD',2,ConditionEnum.Equal,0,0)
    Time1 = dArrTimeStamp1[0]
    Test2, dArrTimeStamp2, dArrTimeStampList2 = STLA_CAN.DBC.FindValueOfSignal(get_message_for_signal('ECU_ELEC_STATE_RCD'),'ECU_ELEC_STATE_RCD',2,ConditionEnum.Unequal,Time1,0)
    Time2 = dArrTimeStamp2[0]

    CursorPosition = replace_zeros([Time1, Time2])
    signal_list = ['IFB_V_VerInfo6or13or20','IFB_Volt_KL30','IFB_Volt_KL15','IFB_Volt_LVCC','RCD_LINE_STATE',
                   'IFB_CCCP_CC_Res','IFB_CCCP_CP_Volt','IFB_CCCP_CP_Fre','IFB_CCCP_CP_Duty',
                   'ECU_ELEC_STATE_RCD','DCDC_STATE_BB','ACDC_CONVERSION_REQUEST','ACDC_CONVERSION_STATE',
                   'DCDC_FAULT_STATE','OBC_FAULT_STATE']
    STLA_CAN.DBC.ExportWfmFile(get_messages_for_signals(signal_list),signal_list,'')
    Sleep(2000)
    STLA_CAN.DBC.ConfigureCursor(CursorEnum.X,CursorPosition)
    STLA_CAN.DBC.ExportImage(ImageFormatEnum.PNG,ColorInversionEnum.ON,'')

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
        f"1. After the OBC wakes up, check the signa period, initial value, and view signa l_ength, Byte_Position and Bit_Position in DBC.\n"+
        f"2. ECU_ELEC_STATE_RCD={ECUElecStateRCD}.\n"+
        f"\n"+
        f"========================================================================="+
        f"\n"+
        f"{all_prints}"
    )


