from CommonFunction.FunctionClass_V2 import *
from UtilityClass.UtilityClass01_DeviceConnectInit import *
from CommonFunction.Common00_Fuction import *
from CommonFunction.Common04_SoftwareCommonFunction import STLA_M_EncapsulationClass


if __name__ == '__main__':

    start_capture_prints()
    STLA_M_EncapsulationClass.InitDevice()
    STLA_M_EncapsulationClass.InitAllCANMessage()
    STLA_M_EncapsulationClass.TestCaseConfig(RecordStart = True, case_name = "STLA-M-VC2_TS_DCC")
    低压辅源.SCPI.Write(':SOUR1:VOLT 12.5;:SOUR1:CURR 3;:OUTP CH1,ON')
    Sleep(8000)
    Test, MeasureKL30Current = 低压辅源.SCPI.Query(':MEAS:CURR? CH1')
    MeasureKL30Current = list(MeasureKL30Current)
    PreTestResult1 = MeasureKL30Current[0] <= 0.05
    print(f"KL30电流:{MeasureKL30Current[0]},测试结果:{PreTestResult1}")

    STLA_CAN.DBC.SetSignal(1, get_message_for_signal('REVEIL_PRINCIPAL'), 'REVEIL_PRINCIPAL', 2)  
    低压辅源.SCPI.Write(':SOUR2:VOLT 5;:SOUR2:CURR 3;:OUTP CH2,ON')
    低压辅源.SCPI.Write(':SOUR3:VOLT 0.6;:SOUR3:CURR 3;:OUTP CH3,ON')
    电阻控制板.Modbus.SetRegister(iID=1,Reg=3072,Data='220')

    STLA_CAN.DBC.SetSignal(1, get_message_for_signal('VOLT_SETPOINT_DCDC_REQ'), 'VOLT_SETPOINT_DCDC_REQ', 14)  
    STLA_CAN.DBC.SetSignal(1, get_message_for_signal('CURR_SETPOINT_DCDC_LV_REQ'), 'CURR_SETPOINT_DCDC_LV_REQ', 250)  

    高压源载一体机.Set.Basic(DCPwrModeEnum.NORM, DCPwrWorkModeEnum.NONE)
    高压源载一体机.Set.Volt(dVolt=365)
    高压源载一体机.Set.Curr(DCPwrSLEnum.SOUR, 15)
    高压源载一体机.Out.Enable(eEnable.ON)
    Sleep(5000)  
    Test, DCDCFaultState = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('DCDC_FAULT_STATE'),'DCDC_FAULT_STATE', 0.0)
    Test, DCDCStateBB1 = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('DCDC_STATE_BB'),'DCDC_STATE_BB', 0.0)
    Sleep(5000)
    PreTestResult2 = DCDCFaultState == 0
    PreTestResult3 = DCDCStateBB1 == 2
    PreCondition = True if PreTestResult1 and PreTestResult2 and PreTestResult3 else False
    print(f"DCDC故障状态:{DCDCFaultState},测试结果:{PreTestResult2}")
    print(f"DCDC状态:{DCDCFaultState},测试结果:{PreTestResult3}")
    
    STLA_CAN.DBC.SetSignal(1, get_message_for_signal('REG_MODE_DCDC_BB_REQ'), 'REG_MODE_DCDC_BB_REQ', 1)  
    Sleep(5000)
    Test, DCDCStateBB2 = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('DCDC_STATE_BB'),'DCDC_STATE_BB', 0.0)
    STLA_CAN.DBC.SetSignal(1, get_message_for_signal('VOLT_SETPOINT_DCDC_REQ'), 'VOLT_SETPOINT_DCDC_REQ', 10.6)  
    Sleep(5000)
    Test, signal_voltage1 = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('DCDC_CONV_LV_VOLT_HD'),'DCDC_CONV_LV_VOLT_HD', 0.0)
    STLA_CAN.DBC.SetSignal(1, get_message_for_signal('VOLT_SETPOINT_DCDC_REQ'), 'VOLT_SETPOINT_DCDC_REQ', 16)  
    Sleep(5000)
    Test, signal_voltage2 = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('DCDC_CONV_LV_VOLT_HD'),'DCDC_CONV_LV_VOLT_HD', 0.0)
    TestResult11 = DCDCStateBB2 == 3
    TestResult12 = abs(signal_voltage1 - 10.6) <= 0.2
    TestResult13 = abs(signal_voltage2 - 16) <= 0.2
    TestResult1 = TestResult11 and TestResult12 and TestResult13
    print(f"DCDC状态:{DCDCStateBB2},测试结果:{TestResult11}")
    print(f"DCDC电压:{signal_voltage1},测试结果:{TestResult12}")
    print(f"DCDC电压:{signal_voltage2},测试结果:{TestResult13}")

    STLA_CAN.DBC.SetSignal(1, get_message_for_signal('VOLT_SETPOINT_DCDC_REQ'), 'VOLT_SETPOINT_DCDC_REQ', 14)  
    STLA_CAN.DBC.SetSignal(1, get_message_for_signal('REG_MODE_DCDC_BB_REQ'), 'REG_MODE_DCDC_BB_REQ', 1)  
    Sleep(5000)
    STLA_CAN.DBC.SetSignal(1, get_message_for_signal('REG_MODE_DCDC_BB_REQ'), 'REG_MODE_DCDC_BB_REQ', 2)  
    Sleep(5000)
    低压源载一体机.Set.Basic(DCPwrModeEnum.NORM, DCPwrWorkModeEnum.NONE)
    低压源载一体机.Set.Curr(DCPwrSLEnum.LOAD, 250)
    低压源载一体机.Out.Enable(eEnable.ON)

    Sleep(1500)
    Test, signal_current = STLA_CAN.DBC.GetSignal(1, get_message_for_signal('DCDC_REAL_LV_CURR_HD'),'DCDC_REAL_LV_CURR_HD', 0.0)
    Test, measure_current = 功率分析仪.Meas.Curr(PACurrEnum.RMS, dealListData([0]*8))
    measure_current = list(measure_current)[4]
    TestResult21 = signal_current > 240
    error = abs(measure_current - signal_current)
    error_percent = (error / abs(signal_current)) * 100
    TestResult22 = error <= 5
    TestResult2 = TestResult21 and TestResult22
    print(f"DCDC电流信号:{signal_current},测试结果:{TestResult21}")
    print(f"功率分析仪测量电流:{measure_current}")
    print(f"误差:{error},误差百分比:{error_percent},测试结果:{TestResult22}")

    Sleep(5000)
    STLA_M_EncapsulationClass.TestCaseConfig(RecordStart = False, case_name = "STLA-M-VC2_TS_DCC")
    STLA_M_EncapsulationClass.CloseAllCANMessage()
    STLA_M_EncapsulationClass.CloseAllDevice()
    
    Test, dArrTimeStamp1, dArrTimeStampList1 = STLA_CAN.DBC.FindValueOfSignal(get_message_for_signal('LD_IORpt_LvVol'),'LD_IORpt_LvVol',16,ConditionEnum.Equal,0,0)
    Test, dArrTimeStamp2, dArrTimeStampList2 = STLA_CAN.DBC.FindValueOfSignal(get_message_for_signal('LD_IORpt_LvCur'),'LD_IORpt_LvCur',240,ConditionEnum.Morethan,0,0)
    Time1 = dArrTimeStamp1[0]
    Time2 = dArrTimeStamp2[0]

    CursorPosition = replace_zeros([Time1, Time2])
    signal_list = ['IFB_V_VerInfo6or13or20','IFB_Volt_KL30','IFB_Volt_KL15','IFB_Volt_LVCC','RCD_LINE_STATE',
                   'IFB_CCCP_CC_Res','OBC_FAULT_STATE','DCDC_FAULT_STATE','LD_IORpt_LvCur','REG_MODE_DCDC_BB_REQ','DCDC_STATE_BB',
                   'LD_IORpt_LvVol']
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
        f"1. DCDC enters BUCK mode, the DC output voltage range is [10.6V,16V].\n"+
        f"2. DCDC enters BUCK mode, the DC output current range is  [0A ,250A].\n"+
        f"\n"+
        f"Note: Output current accuracy\n"+
        f"(1) 5A ≤ Iout ≤50A:≤±10%\n"+
        f"(2) 50A ＜Iout:≤±5A\n"+
        f"Output voltage detection accuracy:≤200mV\n"+
        f"========================================================================="+
        f"\n"+
        f"{all_prints}"
    )








