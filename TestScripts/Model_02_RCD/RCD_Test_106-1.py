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
    Sleep(8000)

    Test, MeasureKL30Current = 低压辅源.SCPI.Query(':MEAS:CURR? CH1')
    MeasureKL30Current = list(MeasureKL30Current)
    PreTestResult1 = MeasureKL30Current[0] <= 0.05
    print(MeasureKL30Current[0], PreTestResult1)

    # 低压辅源.SCPI.Write(':SOUR2:VOLT 5;:SOUR2:CURR 3;:OUTP CH2,ON')
    信号发生器.SCPI.Write(':SOUR1:APPL:SQU 1000,9.4,0,0;:SOUR1:FUNC:SQU:DCYC 78;:OUTP1 ON')
    电阻控制板.Modbus.SetRegister(iID=1,Reg=3072,Data='220')
    Sleep(5500)

    Test, EcuElecStateRCD = STLA_CAN.DBC.GetSignal(1,'SUPV_V2_OBC_DCDC_591','ECU_ELEC_STATE_RCD', 0.0)
    Test, OBCFaultState = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_421','OBC_FAULT_STATE', 0.0)
    Test, DCDCFaultState = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_501','DCDC_FAULT_STATE', 0.0)
    Test, HVBattRechargeWakeup = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_531','HV_BATT_RECHARGE_WAKEUP', 0.0)
    PreTestResult2 = EcuElecStateRCD == 0
    PreTestResult3 = OBCFaultState == 0 and DCDCFaultState == 0
    # PreTestResult4 = HVBattRechargeWakeup == 0

    STLA_CAN.DBC.SetSignal(1, 'VCU_BSI_Wakeup_27A', 'MODE_EPS_REQUEST', 3)
    Sleep(2500)

    Test, HVBattRechargeWakeup11 = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_531','HV_BATT_RECHARGE_WAKEUP', 0.0)
    TestResult11 = HVBattRechargeWakeup11 == 1
    # Sleep(75000)
    Sleep(190000)

    EndTime1 = TimeStamp()
    Test, HVBattRechargeWakeup12 = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_531','HV_BATT_RECHARGE_WAKEUP', 0.0)
    TestResult12 = HVBattRechargeWakeup12 == 1
    TestResult1 = True if TestResult11 and TestResult12 else False

    # debug_break('haaaaaaaaaaaaaaaaaaaaaaaaa')
    Sleep(5000)
    STLA_CAN.DBC.RecordState(AcqEnum.Stop)

    RCD_Exit_EcoMode()
    CloseAllDevice()
    CloseAllCANMessage()

    Test, dArrTimeStamp_Transitory, dArrTimeStampList_Transitory= STLA_CAN.DBC.FindValueOfSignal('SUPV_V2_OBC_DCDC_591','ECU_ELEC_STATE_RCD',2,ConditionEnum.Equal,0,0,[],[])
    Pre_Transitory = dArrTimeStamp_Transitory[0]

    Test, dArrTimeStamp1, dArrTimeStampList1= STLA_CAN.DBC.FindValueOfSignal('DAT_OBC_DCDC_531','HV_BATT_RECHARGE_WAKEUP',1,ConditionEnum.Equal,0,0,[],[])
    StartTime1 = dArrTimeStamp1[0]
    Test, dArrTimeStamp2, dArrTimeStampList2= STLA_CAN.DBC.FindValueOfSignal('DAT_OBC_DCDC_531','HV_BATT_RECHARGE_WAKEUP',0,ConditionEnum.Equal,StartTime1,0,[],[])
    EndTime1 = dArrTimeStamp2[0]
    TestResult2 = abs(abs(EndTime1 - StartTime1) - 180000) < 1500
    
    Test, dArrTimeStamp0, dArrTimeStampList0= STLA_CAN.DBC.FindValueOfSignal('SUPV_V2_OBC_DCDC_591','ECU_ELEC_STATE_RCD',0,ConditionEnum.Equal,0,0,[],[])
    StartTime = dArrTimeStamp0[0]

    PreTestResult2 = (StartTime - Pre_Transitory) > 0
    PreCondition = True if PreTestResult1 and PreTestResult2 and PreTestResult3 else False
    print(f"前置条件1结果:{PreTestResult1}, 前置条件2结果: {PreTestResult2}, 前置条件3结果: {PreTestResult3}")
    print(f"步骤1: HV_BATT_RECHARGE_WAKEUP的状态为{HVBattRechargeWakeup11}")
    print(f"步骤2: HV_BATT_RECHARGE_WAKEUP的由1至0的时间为{EndTime1 - StartTime1}")


    CursorPosition = [Pre_Transitory, StartTime1, StartTime1, EndTime1]
    STLA_CAN.DBC.ExportWfmFile(['IFB_VersionInfo','IFB_Volt','IFB_Volt','IFB_Volt','SUPV_V2_OBC_DCDC_591','IFB_CC_CP','IFB_CC_CP',
                                'IFB_CC_CP','IFB_CC_CP','DYN_E_VCU_342','SUPV_V2_OBC_DCDC_591','DAT_OBC_DCDC_531','SUPV_V2_OBC_DCDC_591',
                                'DAT_OBC_DCDC_531','SUPV_V2_OBC_DCDC_591','DAT_E_VCU_402','VCU_BSI_Wakeup_27A'],
                                ['IFB_V_VerInfo6or13or20','IFB_Volt_KL30','IFB_Volt_KL15','IFB_Volt_LVCC','RCD_LINE_STATE',
                                 'IFB_CCCP_CC_Res','IFB_CCCP_CP_Volt','IFB_CCCP_CP_Fre','IFB_CCCP_CP_Duty','REVEIL_PRINCIPAL',
                                 'ECU_ELEC_STATE_RCD','PI_STATE_INFO_WAKEUP','PI_STATE_INFO_WUP_STATE','HV_BATT_RECHARGE_WAKEUP',
                                 'HV_BATT_CHARGE_WUP_STATE','RECHARGE_HMI_STATE_EVO','MODE_EPS_REQUEST'],
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