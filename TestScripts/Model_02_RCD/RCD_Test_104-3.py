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
    电阻控制板.Modbus.SetRegister(iID=1,Reg=3072,Data='220')
    InitAllCANMessage()
    STLA_CAN.DBC.SetSignal(1, 'TBMU_V2_4F4', 'HV_BATT_CH_NEED_STATE', 0)
    STLA_CAN.DBC.SetSignal(1, 'DAT_E_VCU_402', 'RECHARGE_HMI_STATE_EVO', 0)
    Sleep(8000)

    Test, MeasureKL30Current = 低压辅源.SCPI.Query(':MEAS:CURR? CH1')
    MeasureKL30Current = list(MeasureKL30Current)
    PreTestResult1 = MeasureKL30Current[0] <= 0.05
    print(MeasureKL30Current[0], PreTestResult1)

    信号发生器.SCPI.Write(':SOUR1:APPL:DC 1,1,9.5;:OUTP1 ON')
    电阻控制板.Modbus.SetRegister(iID=1,Reg=3072,Data='220')
    Sleep(35000)
    信号发生器.SCPI.Write(':SOUR1:APPL:DC 1,1,4.0;:OUTP1 ON')
    Sleep(5000)
    StartTime1 = TimeStamp()
    Test, IFB_CVN_CheckSum0 = STLA_CAN.DBC.GetSignal(1,'IFB_CVN','IFB_CVN_CheckSum0', 0.0)
    PreTestResult2 = IFB_CVN_CheckSum0 == 1
    PreCondition = True if PreTestResult1 and PreTestResult2 else False
    print(f"前置条件1结果:{PreTestResult1}, 前置条件2结果: {PreTestResult2}")

    Sleep(40000)
    信号发生器.SCPI.Write(':SOUR1:APPL:SQU 1000,9.5,0,0;:SOUR1:FUNC:SQU:DCYC 78;:OUTP1 ON')
    Sleep(5000)

    EndTime1 = TimeStamp()
    Test, PIStateInfoWakeup1 = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_531','PI_STATE_INFO_WAKEUP', 0.0)
    Test, HVBattRechargeWakeup1 = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_531','HV_BATT_RECHARGE_WAKEUP', 0.0)
    TestResult11 = PIStateInfoWakeup1 == 0
    TestResult12 = HVBattRechargeWakeup1 == 0
    TestResult1 = True if TestResult11 and TestResult12 else False
    print(f"操作步骤1结果:{TestResult11}, 操作步骤2结果: {TestResult12}")

    Sleep(5000)
    STLA_CAN.DBC.RecordState(AcqEnum.Stop)
    RCD_Exit_EcoMode()
    CloseAllDevice()
    CloseAllCANMessage()

    # Test, dArrTimeStamp1, dArrTimeStampList1= STLA_CAN.DBC.FindValueOfSignal('IFB_CVN','IFB_CVN_CheckSum0',0,ConditionEnum.Equal,0,0,[],[])
    # StartTime1 = dArrTimeStamp1[0]
    # Test, dArrTimeStamp2, dArrTimeStampList2= STLA_CAN.DBC.FindValueOfSignal('IFB_CVN','IFB_CVN_CheckSum0',1,ConditionEnum.Equal,StartTime1,0,[],[])
    # EndTime1 = dArrTimeStamp2[0]

    CursorPosition = [StartTime1, EndTime1]
    STLA_CAN.DBC.ExportWfmFile(['IFB_VersionInfo','IFB_Volt','IFB_Volt','IFB_Volt','SUPV_V2_OBC_DCDC_591','IFB_CC_CP','IFB_CC_CP',
                                'IFB_CC_CP','IFB_CC_CP','DYN_E_VCU_342','SUPV_V2_OBC_DCDC_591','DAT_OBC_DCDC_531','SUPV_V2_OBC_DCDC_591',
                                'DAT_OBC_DCDC_531','SUPV_V2_OBC_DCDC_591','DAT_E_VCU_402','DAT_OBC_DCDC_551','IFB_CVN','IFB_CVN'],
                                ['IFB_V_VerInfo6or13or20','IFB_Volt_KL30','IFB_Volt_KL15','IFB_Volt_LVCC','RCD_LINE_STATE',
                                 'IFB_CCCP_CC_Res','IFB_CCCP_CP_Volt','IFB_CCCP_CP_Fre','IFB_CCCP_CP_Duty','REVEIL_PRINCIPAL',
                                 'ECU_ELEC_STATE_RCD','PI_STATE_INFO_WAKEUP','PI_STATE_INFO_WUP_STATE','HV_BATT_RECHARGE_WAKEUP',
                                 'HV_BATT_CHARGE_WUP_STATE','RECHARGE_HMI_STATE_EVO','OBC_PUSH_CHARGE_TYPE','IFB_CVN_CheckSum0','IFB_CVN_CheckSum1'],
                                ''
    )
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