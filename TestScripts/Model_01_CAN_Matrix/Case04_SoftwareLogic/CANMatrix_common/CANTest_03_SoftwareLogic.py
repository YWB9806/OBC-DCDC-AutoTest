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
    print(f"ACDCConversionState == 0, 测试步骤11结果: {TestResult11}")
    print(f"DCDCStateBB == 2, 测试步骤12结果: {TestResult12}")

    电阻控制板.Modbus.SetRegister(iID=1,Reg=3072,Data='220')
    信号发生器.SCPI.Write(':SOUR1:APPL:SQU 1000,12,0,0;:SOUR1:FUNC:SQU:DCYC 60;:OUTP1 ON')
    STLA_CAN.DBC.SetSignal(1, get_message_for_signal('CABLE_LOCK_REQ'), 'CABLE_LOCK_REQ', 1)  
    STLA_CAN.DBC.SetSignal(1, get_message_for_signal('OBC_EVSE_REQUEST'), 'OBC_EVSE_REQUEST', 1)  
    Sleep(5000)
    交流源载一体机.Set.Basic(ACPwrModeEnum.SOUR, ACChannelEnum.EACH, ACCouplingEnum.AC,0, ACPwrWorkModeEnum.CC)
    交流源载一体机.Set.Freq(dFreq=50)
    交流源载一体机.Set.Volt(dealListData([230.0, 230.0, 230.0]),dealListData([0.0, 0.0, 0.0]))
    交流源载一体机.Out.Enable(ACeEnable.ON)
    高压源载一体机.Set.Basic(DCPwrModeEnum.NORM, DCPwrWorkModeEnum.NONE)
    高压源载一体机.Set.Volt(dVolt=350)
    高压源载一体机.Out.Enable(eEnable.ON)
    Sleep(1000)

    交流源载一体机.Set.Volt(dealListData([280.0, 280.0, 280.0]),dealListData([0.0, 0.0, 0.0]))
    Sleep(2000)
    AssignmentCode = 101
    StartTime1 = TimeStamp()     # 获取毫秒级时间戳
    TestResult21 = STLA_M_EncapsulationClass.CheckFaultIsInFaultList(AssignmentCode)
    print(f"IFB_V_VerInfo6or13or20= {TestResult21}")
    STLA_CAN.DBC.SetSignal(1, get_message_for_signal('EFFAC_DEFAUT_DIAG'), 'EFFAC_DEFAUT_DIAG', 1)  
    Sleep(2000)
    TestResult22 = not(STLA_M_EncapsulationClass.CheckFaultIsInFaultList(AssignmentCode))
    TestResult2 = True if TestResult21 and TestResult22 else False
    print(f"IFB_V_VerInfo6or13or20= {TestResult22}")

    STLA_CAN.DBC.SetSignal(1, get_message_for_signal('EFFAC_DEFAUT_DIAG'), 'EFFAC_DEFAUT_DIAG', 0)  
    Sleep(2000)
    EndTime1 = TimeStamp()     # 获取毫秒级时间戳
    TestResult3 = STLA_M_EncapsulationClass.CheckFaultIsInFaultList(AssignmentCode)
    print(f"IFB_V_VerInfo6or13or20= {TestResult3}")


    STLA_M_EncapsulationClass.TestCaseConfig(RecordStart = False, case_name="STLA-M-Common_SoftwareLogic")
    STLA_M_EncapsulationClass.CloseAllCANMessage()
    STLA_M_EncapsulationClass.CloseAllDevice()

    CursorPosition = replace_zeros([StartTime1, EndTime1])
    signal_list = ['IFB_V_VerInfo6or13or20','IFB_Volt_KL30','IFB_Volt_KL15','IFB_Volt_LVCC','RCD_LINE_STATE',
                   'IFB_CCCP_CC_Res','IFB_CCCP_CP_Volt','IFB_CCCP_CP_Fre','IFB_CCCP_CP_Duty',
                   'ECU_ELEC_STATE_RCD','DCDC_STATE_BB','ACDC_CONVERSION_REQUEST','ACDC_CONVERSION_STATE',
                   'DIAG_INTEGRA_ELEC','MODE_DIAG','DIAG_MUX_ON_PWT','EFFAC_DEFAUT_DIAG','OBC_EVSE_MES_AC_VOLTAGE']
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
        f"1. / .\n"+
        f"2. The ECU shall entry in Electronic Integration mode.\n"+
        f"3. The  ECU exit from the Electronic Integration mode.\n"+
        f"\n"+
        f"========================================================================="+
        f"\n"+
        f"{all_prints}"
    )


