from CommonFunction.FunctionClass_V2 import *
from UtilityClass.UtilityClass01_DeviceConnectInit import *
from CommonFunction.Common00_Fuction import *
from CommonFunction.Common01_InitDevice import InitDevice
from CommonFunction.Common01_CloseDevice import CloseAllDevice
from CommonFunction.Common02_InitCANMessage import InitAllCANMessage
from CommonFunction.Common03_CloseCANMessage import CloseAllCANMessage
from CommonFunction.Common04_RCDCommon import RCD_Exit_EcoMode

if __name__ == '__main__':

    InitDevice()
    Sleep(1000)
    Log4NetWrapper.InitLogManage("STLA-M-STEP2.5_DID", get_current_filename())
    STLA_CAN.DBC.ConfigureSetting("STLA-M-STEP2.5_DID", get_current_filename(), RecordFileType.BLF, None)
    STLA_CAN.DBC.SetChannel('All', ['ALL'], RecordEnum.ON)
    STLA_CAN.DBC.RecordState(AcqEnum.Start)

    低压辅源.SCPI.Write(':SOUR1:VOLT 12.5;:SOUR1:CURR 3;:OUTP CH1,ON')
    InitAllCANMessage()
    Sleep(8000)
    Test, MeasureKL30Current = 低压辅源.SCPI.Query(':MEAS:CURR? CH1')
    MeasureKL30Current = list(MeasureKL30Current)
    PreCondition = MeasureKL30Current[0] <= 0.05
    print(MeasureKL30Current[0], PreCondition)

    STLA_CAN.DBC.SetSignal(1, get_message_for_signal('REVEIL_PRINCIPAL'), 'REVEIL_PRINCIPAL', 2)  
    低压辅源.SCPI.Write(':SOUR2:VOLT 5;:SOUR2:CURR 3;:OUTP CH2,ON')
    低压辅源.SCPI.Write(':SOUR3:VOLT 0.6;:SOUR3:CURR 3;:OUTP CH3,ON')
    信号发生器.SCPI.Write(':SOUR1:APPL:SQU 1000,12,0,0;:SOUR1:FUNC:SQU:DCYC 80;:OUTP1 ON')
    电阻控制板.Modbus.SetRegister(iID=1,Reg=3072,Data='220')
    Sleep(5000)

    低压源载一体机.Set.Basic(DCPwrModeEnum.NORM, DCPwrWorkModeEnum.NONE)
    低压源载一体机.Set.Volt(dVolt=18)
    低压源载一体机.Out.Enable(eEnable.ON)
    Sleep(5000)

    Test, DCDC_STATE_BB = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('DCDC_STATE_BB'),'DCDC_STATE_BB', 0.0)
    TestResult1 = DCDC_STATE_BB == 5
    STLA_CAN.DBC.SetMessage(1,'REQ_DIAG_ON_CAN_590',['0'])
    STLA_CAN.DBC.SetSignal(1, get_message_for_signal('DATA_DIAG_1'), 'DATA_DIAG_1', 802)  
    STLA_CAN.DBC.SetSignal(1, get_message_for_signal('DATA_DIAG_2'), 'DATA_DIAG_2', 55335)  
    STLA_CAN.DBC.SetSignal(1, get_message_for_signal('DATA_DIAG_3'), 'DATA_DIAG_3', 0)  
    STLA_CAN.DBC.SetSignal(1, get_message_for_signal('DATA_DIAG_4'), 'DATA_DIAG_4', 0)  
    STLA_CAN.DBC.Trigger(1,'REQ_DIAG_ON_CAN_590', True)
    Sleep(5000)

    Sleep(5000)
    STLA_CAN.DBC.RecordState(AcqEnum.Stop)
    CloseAllDevice()
    CloseAllCANMessage()
    STLA_CAN.DBC.Trigger(1,'REQ_DIAG_ON_CAN_590', False)

    Test, dArrTimeStamp0, dArrTimeStampList0= STLA_CAN.DBC.FindValueOfSignal(get_message_for_signal('DCDC_STATE_BB'),'DCDC_STATE_BB',5,ConditionEnum.Equal,0,0,[],[])
    StartTime1 = dArrTimeStamp0[0]

    Test, EndTime1 = STLA_CAN.DBC.FindMsg('REP_DIAG_ON_CAN_58F',0,0,FindMsgTypeEnum.First,0)
    CursorPosition = replace_zeros([StartTime1, EndTime1])
    signal_list = ['IFB_V_VerInfo6or13or20','IFB_Volt_KL30','IFB_Volt_KL15','IFB_Volt_LVCC','RCD_LINE_STATE',
                   'IFB_CCCP_CC_Res','IFB_CCCP_CP_Volt','IFB_CCCP_CP_Fre','IFB_CCCP_CP_Duty',
                   'ECU_ELEC_STATE_RCD','DCDC_STATE_BB','ACDC_CONVERSION_REQUEST','ACDC_CONVERSION_STATE','DATA_DIAG']
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
    
    Log4NetWrapper.WriteToOutput_KeyInfo(TestResultDisplay, 
        f'Actual test result: 1. .\n'
    )