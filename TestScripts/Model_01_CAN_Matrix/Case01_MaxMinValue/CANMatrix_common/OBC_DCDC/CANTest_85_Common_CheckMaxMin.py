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
    Log4NetWrapper.InitLogManage("STLA-M-VC1_CANMatrix_CheckMaxMin", get_current_filename())
    STLA_CAN.DBC.ConfigureSetting('STLA-M-VC1_CANMatrix_CheckMaxMin', get_current_filename(), RecordFileType.BLF, None)
    STLA_CAN.DBC.SetChannel('All', ['ALL'], RecordEnum.ON)
    STLA_CAN.DBC.RecordState(AcqEnum.Start)
    InitAllCANMessage()
    Sleep(1000)
    
    低压辅源.SCPI.Write(':SOUR1:VOLT 12.5;:SOUR1:CURR 3;:OUTP CH1,ON')
    低压辅源.SCPI.Write(':SOUR2:VOLT 5;:SOUR2:CURR 3;:OUTP CH2,ON')
    低压辅源.SCPI.Write(':SOUR3:VOLT 0.6;:SOUR3:CURR 3;:OUTP CH3,ON')
    STLA_CAN.DBC.SetSignal(1, 'DYN_E_VCU_342', 'REVEIL_PRINCIPAL', 2)
    Sleep(2500)

    高压源载一体机.Set.Basic(DCPwrModeEnum.NORM, DCPwrWorkModeEnum.NONE)
    高压源载一体机.Set.Volt(dVolt=375)
    高压源载一体机.Out.Enable(eEnable.ON)

    STLA_CAN.DBC.SetMessage(1,'DYN_E_VCU_342',['0','0','0','14','0','0','0','0','0'])
    STLA_CAN.DBC.Trigger(1,'DYN_E_VCU_342',True)
    Sleep(5000)
    Test, DCDCStateBB1 = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_541','DCDC_STATE_BB', 0.0)
    PreCondition = DCDCStateBB1 == 2

    STLA_CAN.DBC.SetSignal(1, 'DAT_E_VCU_448', 'REG_MODE_DCDC_BB_REQ', 2)
    Sleep(2000)
    Test, DCDCStateBB3 = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_541','DCDC_STATE_BB', 0.0)
    TestResult1 = DCDCStateBB3 == 3

    低压源载一体机.Set.Curr(DCPwrSLEnum.LOAD, 10)
    低压源载一体机.Out.Enable(eEnable.ON)

    Index = 0
    SingleResultList = []
    DCDCOutputCurrentList = [50, 100, 150, 200, 250]
    CurrentSetListLength = len(DCDCOutputCurrentList)

    for Index in range(CurrentSetListLength):
        SetDCDCOutputCurrent = DCDCOutputCurrentList[Index]
        STLA_CAN.DBC.SetSignal(1, 'DYN_E_VCU_428', 'CURR_SETPOINT_DCDC_LV_REQ', SetDCDCOutputCurrent)
        Sleep(1500)
        低压源载一体机.Set.Curr(DCPwrSLEnum.LOAD, SetDCDCOutputCurrent)
        Sleep(1500)
        Test, ReadDCDCOutputCurrent = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_501','DCDC_REAL_LV_CURR_HD', 0.0)
        SingleResult1 = (ReadDCDCOutputCurrent<=SetDCDCOutputCurrent*1.15) and (ReadDCDCOutputCurrent>=SetDCDCOutputCurrent*0.85)
        SingleResultList.append(SingleResult1)

    TestResult2 = min(SingleResultList)
    print(f"测试步骤1结果: {TestResult1}, 测试步骤2结果: {TestResult2}")

    Sleep(5000)
    STLA_CAN.DBC.RecordState(AcqEnum.Stop)
    CloseAllDevice()
    CloseAllCANMessage()

    StartTime = TimeStamp()     # 获取毫秒级时间戳
    EndTime = TimeStamp()       # 获取毫秒级时间戳
    # Test, StartTime = STLA_CAN.DBC.FindMsg('VERS_OBC_DCDC_0CE',0,0,FindMsgTypeEnum.First,0)
    Test, dArrTimeStamp1, dArrTimeStampList1= STLA_CAN.DBC.FindValueOfSignal('DAT_OBC_DCDC_501','DCDC_REAL_LV_CURR_HD',0,ConditionEnum.Equal,0,0,[],[])
    Test, dArrTimeStamp2, dArrTimeStampList2= STLA_CAN.DBC.FindValueOfSignal('DAT_OBC_DCDC_501','DCDC_REAL_LV_CURR_HD',240,ConditionEnum.Morethan,0,0,[],[])
    StartTime = dArrTimeStamp1[0]
    EndTime = dArrTimeStamp2[0]

    CursorPosition = [StartTime, EndTime]
    STLA_CAN.DBC.ExportWfmFile(['IFB_VersionInfo','IFB_Volt','IFB_Volt','IFB_Volt','SUPV_V2_OBC_DCDC_591','IFB_CC_CP','IFB_CC_CP',
                                'IFB_CC_CP','IFB_CC_CP','DYN_E_VCU_342','SUPV_V2_OBC_DCDC_591','DAT_OBC_DCDC_501'],
                                ['IFB_V_VerInfo6or13or20','IFB_Volt_KL30','IFB_Volt_KL15','IFB_Volt_LVCC','RCD_LINE_STATE',
                                 'IFB_CCCP_CC_Res','IFB_CCCP_CP_Volt','IFB_CCCP_CP_Fre','IFB_CCCP_CP_Duty','REVEIL_PRINCIPAL',
                                 'ECU_ELEC_STATE_RCD','DCDC_REAL_LV_CURR_HD'],
                                ''
    )
    Sleep(2000)
    STLA_CAN.DBC.ConfigureCursor(CursorEnum.X,CursorPosition)
    STLA_CAN.DBC.ExportImage(ImageFormatEnum.PNG,ColorInversionEnum.ON,'')

    # print(f" 前置步骤结果：{PreCondition}, 测试步骤1结果: {TestResult1}")
    TestResult = True if PreCondition and TestResult1 and TestResult2  else False
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
