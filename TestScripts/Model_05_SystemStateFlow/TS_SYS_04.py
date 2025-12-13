from CommonFunction.FunctionClass_V2 import *
from UtilityClass.UtilityClass01_DeviceConnectInit import *
from CommonFunction.Common00_Fuction import *
from CommonFunction.Common04_SoftwareCommonFunction import STLA_M_EncapsulationClass


if __name__ == '__main__':

    start_capture_prints()    
    debug_break("手动打开ATE台架上的万用表")
    SetCCResistance = 0
    ResistanceDictSequence1 = {}
    MaxResistance = 9
    Step = 0.5
    for resistance in STLA_M_EncapsulationClass.float_range(SetCCResistance, MaxResistance, Step):
        电阻控制板.Modbus.SetRegister(iID=1, Reg=3072, Data=f'{resistance}')
        Sleep(3000)
        Test, ReadRes = 万用表.Utility.Command(DMMCommandWREnum.R, 'MEAS:RES?')
        print(f"设置值: {resistance}Ω, 测量值: {ReadRes}Ω")
        ResistanceDictSequence1[resistance] = float(ReadRes.strip())
        # Sleep(1500)

    Sleep(5000)
    debug_break("手动关闭ATE台架上的万用表")
    StartTime = TimeStamp()
    STLA_M_EncapsulationClass.InitDevice()
    STLA_M_EncapsulationClass.InitAllCANMessage()
    STLA_M_EncapsulationClass.TestCaseConfig(RecordStart = True, case_name = "STLA-M-VC2_TS_SystemStateFlow")
    低压辅源.SCPI.Write(':SOUR1:VOLT 12.5;:SOUR1:CURR 3;:OUTP CH1,ON')
    低压辅源.SCPI.Write(':SOUR2:VOLT 5;:SOUR2:CURR 3;:OUTP CH2,ON')
    低压辅源.SCPI.Write(':SOUR3:VOLT 0.6;:SOUR3:CURR 3;:OUTP CH3,ON')
    Sleep(2000)

    TestResult1Sequence = []
    TestResult2Sequence = []
    ResistanceDictSequence2 = {}
    for resistance in STLA_M_EncapsulationClass.float_range(SetCCResistance, MaxResistance, Step):
        电阻控制板.Modbus.SetRegister(iID=1, Reg=3072, Data=f'{resistance}')
        Sleep(3000)
        Test, OBCFaultState = STLA_CAN.DBC.GetSignal(1, get_message_for_signal('OBC_FAULT_STATE'), 'OBC_FAULT_STATE', 0.0)
        Test, DCDCFaultState = STLA_CAN.DBC.GetSignal(1, get_message_for_signal('DCDC_FAULT_STATE'), 'DCDC_FAULT_STATE', 0.0)
        Test, OBCChgrConnConf = STLA_CAN.DBC.GetSignal(1, get_message_for_signal('OBC_CHRG_CONN_CONF'), 'OBC_CHRG_CONN_CONF', 0.0)
        Test, CCS_V2L_PLUG_Detected = STLA_CAN.DBC.GetSignal(1, get_message_for_signal('CCS_V2L_PLUG_DETECTED'), 'CCS_V2L_PLUG_DETECTED', 0.0)
        Test, IFB_CCCP_CC_Res = STLA_CAN.DBC.GetSignal(1, 'IFB_CC_CP', 'IFB_CCCP_CC_Res', 0.0)
        ResistanceDictSequence2[resistance] = IFB_CCCP_CC_Res
        print(f"设置值: {resistance}Ω, 测量值: {IFB_CCCP_CC_Res}Ω")
        CheckFaultState = OBCFaultState==0 and DCDCFaultState==0
        TestResult1Sequence.append(CheckFaultState)
        TestResult2Sequence.append(OBCChgrConnConf == 3)
   
    result_str = "电阻测试结果汇总:\n"
    result_str += "="*80 + "\n"
    result_str += "设置电阻(Ω) | 未上电测量值(Ω) | 上电后测量值(Ω) | 误差值(%) | 误差状态\n"
    result_str += "-"*80 + "\n"
    tolerance_results = STLA_M_EncapsulationClass.check_resistance_tolerance(ResistanceDictSequence1, ResistanceDictSequence2)
    for resistance in sorted(ResistanceDictSequence1.keys()):
        unpowered_value = ResistanceDictSequence1.get(resistance, "N/A")
        powered_value = ResistanceDictSequence2.get(resistance, "N/A")
        if isinstance(unpowered_value, (int, float)) and isinstance(powered_value, (int, float)):
            error_percent = abs(unpowered_value - powered_value) / unpowered_value * 100
        else:
            error_percent = "N/A"
        tolerance_status = "符合" if tolerance_results.get(resistance, False) else "超出"
        result_str += f"{resistance:^11} | {unpowered_value:^15.2f} | {powered_value:^15.2f} | {error_percent if isinstance(error_percent, str) else error_percent:^9.2f}% | {tolerance_status:^8}\n"
    print(result_str)
    Sleep(5000)
    STLA_M_EncapsulationClass.TestCaseConfig(RecordStart = False, case_name="STLA-M-VC2_TS_SystemStateFlow")
    STLA_M_EncapsulationClass.CloseAllCANMessage()
    STLA_M_EncapsulationClass.CloseAllDevice()

    Test, dArrTimeStamp1, dArrTimeStampList1 = STLA_CAN.DBC.FindValueOfSignal(get_message_for_signal('OBC_CHRG_CONN_CONF'),'OBC_CHRG_CONN_CONF',3,ConditionEnum.Equal,StartTime,0)
    Test, dArrTimeStamp2, dArrTimeStampList2 = STLA_CAN.DBC.FindValueOfSignal(get_message_for_signal('OBC_CHRG_CONN_CONF'),'OBC_CHRG_CONN_CONF',3,ConditionEnum.Equal,StartTime,0)
    Time1 = dArrTimeStamp1[10]
    Time2 = dArrTimeStamp2[20]

    CursorPosition = replace_zeros([Time1, Time2])
    signal_list = ['IFB_V_VerInfo6or13or20','IFB_Volt_KL30','IFB_Volt_KL15','IFB_Volt_LVCC','RCD_LINE_STATE',
                   'IFB_CCCP_CC_Res','OBC_FAULT_STATE','DCDC_FAULT_STATE','OBC_CHRG_CONN_CONF','CCS_V2L_PLUG_DETECTED']
    message_list = get_messages_for_signals(signal_list)
    STLA_CAN.DBC.ExportWfmFile(message_list,signal_list,'')
    Sleep(2000)
    STLA_CAN.DBC.ConfigureCursor(CursorEnum.X,CursorPosition)
    STLA_CAN.DBC.ExportImage(ImageFormatEnum.PNG,ColorInversionEnum.ON,'')

    TestResult1 = min(TestResult1Sequence)
    TestResult2 = min(TestResult2Sequence)
    print(f"测试步骤1结果: {TestResult1}, 测试步骤2结果: {TestResult2}")
    TestResult = True if TestResult1 and TestResult2 else False
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
        f"1.Report CCS_PlugDetected(OBC_CHRG_CONN_CONF)=UNKNOWN.==>{TestResult2}\n"+
        f"\n"+
        f"========================================================================="+
        f"\n"+
        f"{all_prints}"
    )


