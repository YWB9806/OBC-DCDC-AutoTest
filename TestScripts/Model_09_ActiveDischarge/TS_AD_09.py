from CommonFunction.FunctionClass_V2 import *
from UtilityClass.UtilityClass01_DeviceConnectInit import *
from CommonFunction.Common00_Fuction import *
from CommonFunction.Common04_SoftwareCommonFunction import STLA_M_EncapsulationClass


if __name__ == '__main__':

    start_capture_prints()
    STLA_M_EncapsulationClass.InitDevice()
    STLA_M_EncapsulationClass.InitAllCANMessage()
    STLA_M_EncapsulationClass.TestCaseConfig(RecordStart = True, case_name = "STLA-M-VC2_TS_AD")
    低压辅源.SCPI.Write(':SOUR1:VOLT 12.5;:SOUR1:CURR 3;:OUTP CH1,ON')
    Sleep(8000)
    Test, MeasureKL30Current = 低压辅源.SCPI.Query(':MEAS:CURR? CH1')
    MeasureKL30Current = list(MeasureKL30Current)
    PreTestResult1 = MeasureKL30Current[0] <= 0.05
    print(MeasureKL30Current[0], PreTestResult1)

    STLA_CAN.DBC.SetSignal(1, get_message_for_signal('REVEIL_PRINCIPAL'), 'REVEIL_PRINCIPAL', 2)  
    低压辅源.SCPI.Write(':SOUR2:VOLT 5;:SOUR2:CURR 3;:OUTP CH2,ON')
    低压辅源.SCPI.Write(':SOUR3:VOLT 0.6;:SOUR3:CURR 3;:OUTP CH3,ON')
    信号发生器.SCPI.Write(':SOUR1:APPL:SQU 1000,12,0,0;:SOUR1:FUNC:SQU:DCYC 80;:OUTP1 ON')
    电阻控制板.Modbus.SetRegister(iID=1,Reg=3072,Data='220')
    Sleep(5000)
    高压源载一体机.Set.Basic(DCPwrModeEnum.NORM, DCPwrWorkModeEnum.NONE)
    高压源载一体机.Set.Volt(dVolt=60)
    高压源载一体机.Out.Enable(eEnable.ON)
    Sleep(2000)
    STLA_CAN.DBC.SetSignal(1, get_message_for_signal('REG_MODE_DCDC_BB_REQ'), 'REG_MODE_DCDC_BB_REQ', 2)  
    Sleep(2000)
    Test, DCDCStateBB0 = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('DCDC_STATE_BB'),'DCDC_STATE_BB', 0.0)
    Test, OBCFaultState = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('OBC_FAULT_STATE'),'OBC_FAULT_STATE', 0.0)
    Test, DCDCFaultState = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('DCDC_FAULT_STATE'),'DCDC_FAULT_STATE', 0.0)
    PreTestResult1 = DCDCStateBB0 == 3
    PreTestResult2 = OBCFaultState == 0
    PreTestResult3 = DCDCFaultState == 0
    PreCondition = True if PreTestResult1 and PreTestResult2 and PreTestResult3 else False
    print(f"DCDC_STATE_BB={DCDCStateBB0}, 测试结果: {PreTestResult1}")
    print(f"OBC_FAULT_STATE={OBCFaultState}, 测试结果: {PreTestResult2}")
    print(f"DCDC_FAULT_STATE={DCDCFaultState}, 测试结果: {PreTestResult3}")
    
    STLA_CAN.DBC.SetSignal(1, get_message_for_signal('HV_ACTIVE_DISCH_REQ'), 'HV_ACTIVE_DISCH_REQ', 1)  
    STLA_CAN.DBC.SetSignal(1, get_message_for_signal('ETAT_DISCONT_BATT_HT'), 'ETAT_DISCONT_BATT_HT', 0)  
    Sleep(200)
    高压源载一体机.Out.Enable(eEnable.OFF)
    Sleep(1500)
    Test, DCDCStateBB1 = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('DCDC_STATE_BB'),'DCDC_STATE_BB', 0.0)
    TestResult1 = DCDCStateBB1 == 6
    print(f"DCDC_STATE_BB={DCDCStateBB1}, 测试结果: {TestResult1}")
    Sleep(5000)
    STLA_CAN.DBC.SetSignal(1, get_message_for_signal('HV_ACTIVE_DISCH_REQ'), 'HV_ACTIVE_DISCH_REQ', 0)  
    STLA_CAN.DBC.SetSignal(1, get_message_for_signal('REG_MODE_DCDC_BB_REQ'), 'REG_MODE_DCDC_BB_REQ', 0)  
    Sleep(1500)
    Test, DCDCStateBB2 = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('DCDC_STATE_BB'),'DCDC_STATE_BB', 0.0)
    TestResult2 = DCDCStateBB2 == 2
    print(f"DCDC_STATE_BB={DCDCStateBB2}, 测试结果: {TestResult2}")


    Sleep(5000)
    STLA_M_EncapsulationClass.TestCaseConfig(RecordStart = False, case_name = "STLA-M-VC2_TS_AD")
    STLA_M_EncapsulationClass.CloseAllCANMessage()
    STLA_M_EncapsulationClass.CloseAllDevice()

    Test, dArrTimeStamp1, dArrTimeStampList1 = STLA_CAN.DBC.FindValueOfSignal(get_message_for_signal('DCDC_STATE_BB'),'DCDC_STATE_BB',6,ConditionEnum.Equal,0,0)
    Time1 = dArrTimeStamp1[0]
    Test, dArrTimeStamp2, dArrTimeStampList2 = STLA_CAN.DBC.FindValueOfSignal(get_message_for_signal('DCDC_STATE_BB'),'DCDC_STATE_BB',2,ConditionEnum.Equal,Time1,0)
    Time2 = dArrTimeStamp2[0]

    CursorPosition = replace_zeros([Time1, Time2])
    signal_list = ['IFB_V_VerInfo6or13or20','IFB_Volt_KL30','IFB_Volt_KL15','IFB_Volt_LVCC','RCD_LINE_STATE',
                   'OBC_FAULT_STATE','DCDC_FAULT_STATE',
                   'REG_MODE_DCDC_BB_REQ','DCDC_STATE_BB','HV_ACTIVE_DISCH_REQ']
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
        f"1-4:DCDC_STATE_BB={DCDCStateBB1}, then DCDC_STATE_BB={DCDCStateBB2}.\n"+
        f"========================================================================="+
        f"\n"+
        f"{all_prints}"
    )

 