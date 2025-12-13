from CommonFunction.FunctionClass_V2 import *
from UtilityClass.UtilityClass01_DeviceConnectInit import *
from CommonFunction.Common00_Fuction import *
from CommonFunction.Common01_InitDevice import InitDevice
from CommonFunction.Common01_CloseDevice import CloseAllDevice
from CommonFunction.Common02_InitCANMessage import InitAllCANMessage
from CommonFunction.Common03_CloseCANMessage import CloseAllCANMessage


if __name__ == '__main__':
    InitDevice()
    Sleep(1000)
    Log4NetWrapper.InitLogManage("STLA-M-CANMatrix_Common", get_current_filename())
    STLA_CAN.DBC.ConfigureSetting('STLA-M-CANMatrix_Common', get_current_filename(), RecordFileType.BLF, None)
    STLA_CAN.DBC.SetChannel('All', ['ALL'], RecordEnum.ON)
    STLA_CAN.DBC.RecordState(AcqEnum.Start)

    低压辅源.SCPI.Write(':SOUR1:VOLT 12.5;:SOUR1:CURR 3;:OUTP CH1,ON')
    InitAllCANMessage()
    Sleep(8000)

    Test, MeasureKL30Current = 低压辅源.SCPI.Query(':MEAS:CURR? CH1')
    MeasureKL30Current = list(MeasureKL30Current)
    PreTestResult = MeasureKL30Current[0] <= 0.05
    print(MeasureKL30Current[0], PreTestResult)

    低压辅源.SCPI.Write(':SOUR2:VOLT 5;:SOUR2:CURR 3;:OUTP CH2,ON')
    低压辅源.SCPI.Write(':SOUR3:VOLT 0.6;:SOUR3:CURR 3;:OUTP CH3,ON')
    电阻控制板.Modbus.SetRegister(iID=1,Reg=3072,Data='220')
    Sleep(5500)
    Test, OBCEvseDCMaxCurrent = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_421','OBC_EVSE_DC_MAX_CURRENT', 0.0)
    TestResult = OBCEvseDCMaxCurrent == 0 # 0x7D0
    print(f"OBC_EVSE_DC_MAX_CURRENT: {OBCEvseDCMaxCurrent}, TestResult: {TestResult}")
    
    StartTime = TimeStamp()     # 获取毫秒级时间戳
    Sleep(15000)
    EndTime = TimeStamp()       # 获取毫秒级时间戳
    Sleep(5000)
    STLA_CAN.DBC.RecordState(AcqEnum.Stop)
    CloseAllDevice()
    CloseAllCANMessage()

    # Test, dArrTimeStamp1, dArrTimeStampList1= STLA_CAN.DBC.FindValueOfSignal('DAT_OBC_DCDC_281','DCDC_CONV_LV_VOLT_HD',14,ConditionEnum.Equal,0,0,[],[])
    # Test, dArrTimeStamp2, dArrTimeStampList2= STLA_CAN.DBC.FindValueOfSignal('DYN_E_VCU_428','CURR_SETPOINT_DCDC_LV_REQ',400,ConditionEnum.Equal,0,0,[],[])
    # StartTime = dArrTimeStamp1[0]
    # FindStateTime = dArrTimeStamp2[0]
    Test, StartTime = STLA_CAN.DBC.FindMsg('DAT_OBC_DCDC_421',0,0,FindMsgTypeEnum.First,0)


    CursorPosition = [StartTime, EndTime]
    STLA_CAN.DBC.ExportWfmFile(['IFB_VersionInfo','IFB_Volt','IFB_Volt','IFB_Volt','SUPV_V2_OBC_DCDC_591','IFB_CC_CP','IFB_CC_CP',
                                'IFB_CC_CP','IFB_CC_CP','DYN_E_VCU_342','SUPV_V2_OBC_DCDC_591','DAT_OBC_DCDC_421'],
                                ['IFB_V_VerInfo6or13or20','IFB_Volt_KL30','IFB_Volt_KL15','IFB_Volt_LVCC','RCD_LINE_STATE',
                                 'IFB_CCCP_CC_Res','IFB_CCCP_CP_Volt','IFB_CCCP_CP_Fre','IFB_CCCP_CP_Duty','REVEIL_PRINCIPAL',
                                 'ECU_ELEC_STATE_RCD','OBC_EVSE_DC_MAX_CURRENT'],
                                ''
    )
    Sleep(2000)
    STLA_CAN.DBC.ConfigureCursor(CursorEnum.X,CursorPosition)
    STLA_CAN.DBC.ExportImage(ImageFormatEnum.PNG,ColorInversionEnum.ON,'')

    # print(f" 前置步骤结果：{PreCondition}, 测试步骤1结果: {TestResult1}")
    # TestResult = True if PreCondition and TestResult1  else False
    if TestResult == True:
        TestResultDisplay = '合格'
        Log4NetWrapper.WriteToOutput(f'测试结果:{TestResultDisplay}')
        print(TestResultDisplay)
    else:
        TestResultDisplay = '不合格'
        Log4NetWrapper.WriteToOutput(f'测试结果:{TestResultDisplay}')
        print(TestResultDisplay)

    # Log4NetWrapper.WriteToOutput_KeyInfo(TestResultDisplay, 
    #     f'Actual test result: 1. In Standby mode, OBC shall have no power output, the output current of EVSE_CCS_PLUGIN_CURRENT_ST is {EVSE_CCS_PLUGIN_CURRENT_ST}A.\n'
    # )
