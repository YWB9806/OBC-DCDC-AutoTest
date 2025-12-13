from CommonFunction.FunctionClass_V2 import *
from UtilityClass.UtilityClass01_DeviceConnectInit import *
# from UtilityClass.UtilityClass02_TSCANConnectInit import *
from CommonFunction.Common00_Fuction import *
from CommonFunction.Common01_InitDevice import InitDevice
from CommonFunction.Common01_CloseDevice import CloseAllDevice
from CommonFunction.Common02_InitCANMessage import InitAllCANMessage
from CommonFunction.Common03_CloseCANMessage import CloseAllCANMessage
from CommonFunction.Common04_RCDCommon import RCD_Exit_EcoMode

if __name__ == '__main__':

    InitDevice()
    Sleep(1000)
    Log4NetWrapper.InitLogManage("STLA-M-STEP2.5_RCD", get_current_filename())
    STLA_CAN.DBC.ConfigureSetting("STLA-M-STEP2.5_RCD", get_current_filename(), RecordFileType.BLF, None)
    STLA_CAN.DBC.SetChannel('All', ['ALL'], RecordEnum.ON)
    STLA_CAN.DBC.RecordState(AcqEnum.Start)

    低压辅源.SCPI.Write(':SOUR1:VOLT 12.5;:SOUR1:CURR 3;:OUTP CH1,ON')
    # 低压辅源.SCPI.Write(':SOUR2:VOLT 5;:SOUR2:CURR 3;:OUTP CH2,ON')
    # 低压辅源.SCPI.Write(':SOUR3:VOLT 0.6;:SOUR3:CURR 3;:OUTP CH3,ON')
    InitAllCANMessage()
    STLA_CAN.DBC.SetSignal(1, 'TBMU_V2_4F4', 'HV_BATT_CH_NEED_STATE', 1)
    Sleep(8000)

    Test, MeasureKL30Current = 低压辅源.SCPI.Query(':MEAS:CURR? CH1')
    MeasureKL30Current = list(MeasureKL30Current)
    PreTestResult1 = MeasureKL30Current[0] <= 0.05
    print(MeasureKL30Current[0], PreTestResult1)

    低压辅源.SCPI.Write(':SOUR2:VOLT 5;:SOUR2:CURR 3;:OUTP CH2,ON')
    电阻控制板.Modbus.SetRegister(iID=1,Reg=3072,Data='220')
    Sleep(2000)

    低压辅源.SCPI.Write(':SOUR2:VOLT 2.0;:SOUR2:CURR 3;:OUTP CH2,ON')

    Test, EcuElecStateRCD = STLA_CAN.DBC.GetSignal(1,'SUPV_V2_OBC_DCDC_591','ECU_ELEC_STATE_RCD', 0.0)
    Test, OBCFaultState = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_421','OBC_FAULT_STATE', 0.0)
    Test, DCDCFaultState = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_501','DCDC_FAULT_STATE', 0.0)
    Test, PIStateInfoWakeup = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_531','PI_STATE_INFO_WAKEUP', 0.0)
    Test, RCDLineState = STLA_CAN.DBC.GetSignal(1,'SUPV_V2_OBC_DCDC_591','RCD_LINE_STATE', 0.0)
    PreTestResult2 = EcuElecStateRCD == 2
    PreTestResult3 = OBCFaultState == 0 and DCDCFaultState == 0
    PreTestResult4 = PIStateInfoWakeup == 0
    PreTestResult5 = RCDLineState == 1

    debug_break('To simulate the PLUG_IN BEPR button press action,PUSH_RECH ground connected')
    Sleep(5000)
    
    Test, PIStateInfoWakeup1 = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_531','PI_STATE_INFO_WAKEUP', 0.0)
    TestResult1 = PIStateInfoWakeup1 == 1
    Sleep(75000)

    STLA_CAN.DBC.RecordState(AcqEnum.Stop)
    RCD_Exit_EcoMode()
    CloseAllDevice()
    CloseAllCANMessage()

    Test, dArrTimeStamp_Transitory, dArrTimeStampList_Transitory= STLA_CAN.DBC.FindValueOfSignal('SUPV_V2_OBC_DCDC_591','ECU_ELEC_STATE_RCD',2,ConditionEnum.Equal,0,0,[],[])
    Pre_Transitory = dArrTimeStamp_Transitory[0]

    Test, dArrTimeStamp1, dArrTimeStampList1= STLA_CAN.DBC.FindValueOfSignal('DAT_OBC_DCDC_531','PI_STATE_INFO_WAKEUP',1,ConditionEnum.Equal,0,0,[],[])
    StartTime1 = dArrTimeStamp1[0]
    Test, dArrTimeStamp2, dArrTimeStampList2= STLA_CAN.DBC.FindValueOfSignal('DAT_OBC_DCDC_531','PI_STATE_INFO_WAKEUP',0,ConditionEnum.Equal,StartTime1,0,[],[])
    EndTime1 = dArrTimeStamp2[0]
    TestResult2 = abs(abs(EndTime1 - StartTime1) - 60000) < 1500
    
    Test, dArrTimeStamp0, dArrTimeStampList0= STLA_CAN.DBC.FindValueOfSignal('SUPV_V2_OBC_DCDC_591','ECU_ELEC_STATE_RCD',0,ConditionEnum.Equal,0,0,[],[])
    StartTime = dArrTimeStamp0[0]

    PreTestResult2 = (StartTime - Pre_Transitory) > 0
    PreCondition = True if PreTestResult1 and PreTestResult2 and PreTestResult3 and PreTestResult4 and PreTestResult5 else False
    print(f"前置条件1结果:{PreTestResult1}, 前置条件2结果: {PreTestResult2}, 前置条件3结果: {PreTestResult3}, 前置条件4结果: {PreTestResult4}, 前置条件5结果: {PreTestResult5}")
    print(f"步骤1: PI_STATE_INFO_WAKEUP的状态为{PIStateInfoWakeup}")
    print(f"步骤2: PI_STATE_INFO_WAKEUP的状态从1变为0的时间间隔为{abs(EndTime1 - StartTime1)}秒")
    
    CursorPosition = [StartTime1, EndTime1]
    STLA_CAN.DBC.ExportWfmFile(['IFB_VersionInfo','IFB_Volt','IFB_Volt','IFB_Volt','SUPV_V2_OBC_DCDC_591','IFB_CC_CP','IFB_CC_CP',
                                'IFB_CC_CP','IFB_CC_CP','DYN_E_VCU_342','SUPV_V2_OBC_DCDC_591','DAT_OBC_DCDC_531','SUPV_V2_OBC_DCDC_591',
                                'DAT_OBC_DCDC_531','SUPV_V2_OBC_DCDC_591','DAT_E_VCU_402','DAT_OBC_DCDC_551'],
                                ['IFB_V_VerInfo6or13or20','IFB_Volt_KL30','IFB_Volt_KL15','IFB_Volt_LVCC','RCD_LINE_STATE',
                                 'IFB_CCCP_CC_Res','IFB_CCCP_CP_Volt','IFB_CCCP_CP_Fre','IFB_CCCP_CP_Duty','REVEIL_PRINCIPAL',
                                 'ECU_ELEC_STATE_RCD','PI_STATE_INFO_WAKEUP','PI_STATE_INFO_WUP_STATE','HV_BATT_RECHARGE_WAKEUP',
                                 'HV_BATT_CHARGE_WUP_STATE','RECHARGE_HMI_STATE_EVO','OBC_PUSH_CHARGE_TYPE'],
                                ''
    )
    Sleep(2000)
    STLA_CAN.DBC.ConfigureCursor(CursorEnum.X,CursorPosition)
    STLA_CAN.DBC.ExportImage(ImageFormatEnum.PNG,ColorInversionEnum.ON,'')

    print(f"前置条件结果:{PreCondition}, 测试步骤1结果: {TestResult1}, 测试步骤2结果: {TestResult2}")
    TestResult = True if PreCondition and TestResult1 and TestResult2 else False
    if TestResult == True:
        TestResultDisplay = '合格'
        print(TestResultDisplay)
    else:
        TestResultDisplay = '不合格'
        print(TestResultDisplay)
    
    Log4NetWrapper.WriteToOutput_KeyInfo(TestResultDisplay, 
        f'Actual test result: 1. .\n'
    )