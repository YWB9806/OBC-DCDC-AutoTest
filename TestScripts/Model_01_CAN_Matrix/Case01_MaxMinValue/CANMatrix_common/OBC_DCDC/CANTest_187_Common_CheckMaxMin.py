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
    
    # 前置步骤
    低压辅源.SCPI.Write(':SOUR1:VOLT 12.5;:SOUR1:CURR 3;:OUTP CH1,ON')
    低压辅源.SCPI.Write(':SOUR2:VOLT 5;:SOUR2:CURR 3;:OUTP CH2,ON')
    低压辅源.SCPI.Write(':SOUR3:VOLT 0.6;:SOUR3:CURR 3;:OUTP CH3,ON')
    信号发生器.SCPI.Write(':SOUR1:APPL:SQU 1000,18.1,0,0;:SOUR1:FUNC:SQU:DCYC 80;:OUTP1 ON')
    电阻控制板.Modbus.SetRegister(iID=1,Reg=3072,Data='220')
    STLA_CAN.DBC.SetSignal(1, 'DYN_E_VCU_342', 'REVEIL_PRINCIPAL', 2)
    STLA_CAN.DBC.SetSignal(1, 'DAT_E_VCU_422', 'CONFIG_VHL', 0)
    Sleep(5000)

    Test, OBCFaultState = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_421','OBC_FAULT_STATE', 0.0)
    Test, DCDCFaultState = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_501','DCDC_FAULT_STATE', 0.0)
    Test, AcdcConversionState = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_501','ACDC_CONVERSION_STATE', 0.0)
    PreTestResult1 = OBCFaultState == 0 and DCDCFaultState == 0
    PreTestResult2 = AcdcConversionState == 0
    PreCondition = True if PreTestResult1 and PreTestResult2 else False
    print(f"前置条件1结果:{PreTestResult1}, 前置条件2结果: {PreTestResult2}")

    # 清除历史故障
    def ClearDEHFaultList():
        继电器控制板.Modbus.SetRegister(iID=1,Reg=3072,Data='6132')
        Sleep(1000)
        STLA_CAN.DBC.SetSignal(1, 'VCU_BSI_Wakeup_27A', 'ETAT_PRINCIP_SEV', 1)
        for i in range(3):
            STLA_CAN.DBC.SendMessage(1, 'ELECTRON_BSI_092', ['1','0','0'], 1, 100)
            Sleep(200)
        Test, FaultClear = STLA_CAN.DBC.GetSignal(1,'IFB_OBC_Cmd','IFB_OBCCmd_OBC_FaultClear', 0.0)
        CheckFaultIsnotCleared = FaultClear==1
        Sleep(1000)
        STLA_CAN.DBC.SendMessage(1, 'REQ_DIAG_ON_CAN_590', ['793','527','0','0'], 1, 100)
        Sleep(200)
        Test, ArrData1 = STLA_CAN.DBC.GetMessage(1, 'REP_DIAG_ON_CAN_58F')
        继电器控制板.Modbus.SetRegister(iID=1,Reg=3072,Data='8181')
        Sleep(1000)

    ClearDEHFaultList()

    低压辅源.SCPI.Write(':SOUR2:VOLT 2;:SOUR2:CURR 3;:OUTP CH2,ON')
    Sleep(75000)
    低压辅源.SCPI.Write(':SOUR2:VOLT 5;:SOUR2:CURR 3;:OUTP CH2,ON')
    Sleep(5000)
    Test, ArrData1 = STLA_CAN.DBC.GetMessage(1, 'NEW_JDD_OBC_DCDC_5B1')
    TestResult1 = ArrData1[0]!=0

    STLA_CAN.DBC.SetMessage(1,'V2_BSI_552',['0','0','0'])
    STLA_CAN.DBC.SetSignal(1, 'V2_BSI_552', 'KILOMETRAGE', 838860)
    STLA_CAN.DBC.Trigger(1, 'V2_BSI_552', True)
    STLA_CAN.DBC.Trigger(1, 'DAT_E_VCU_448', False)
    Sleep(5000)

    def CheckIsNotCodeResult():
        Index = 0
        LengthData = 30
        ResultData = []
        for i in range(LengthData):
            Test, GetData = STLA_CAN.DBC.GetSignal(1,'IFB_VersionInfo','IFB_V_VerInfo6or13or20', 0.0)
            Sleep(200)
            ResultData.append(GetData)
            Index += 1
        Sleep(1500)
        Index = 0
        LengData = len(ResultData)
        for i in range(LengData):
            GetData = ResultData[Index]
            CheckIsNotCode = (GetData == AssignmentCode)
            if CheckIsNotCode:
                CheckIsNotCodeResult = True
                break
            else:
                CheckIsNotCodeResult = False
            Index += 1
        return CheckIsNotCodeResult


    AssignmentCode = 90
    TestResult2 = CheckIsNotCodeResult()

    Sleep(5000)
    STLA_CAN.DBC.RecordState(AcqEnum.Stop)
    CloseAllDevice()
    CloseAllCANMessage()

    StartTime = TimeStamp()     # 获取毫秒级时间戳
    EndTime = TimeStamp()       # 获取毫秒级时间戳
    # Test, StartTime = STLA_CAN.DBC.FindMsg('VERS_OBC_DCDC_0CE',0,0,FindMsgTypeEnum.First,0)
    Test, dArrTimeStamp1, dArrTimeStampList1= STLA_CAN.DBC.FindValueOfSignal('NEW_JDD_OBC_DCDC_5B1','KILOMETRAGE_JDD',0,ConditionEnum.Equal,0,0,[],[])
    Test, dArrTimeStamp2, dArrTimeStampList2= STLA_CAN.DBC.FindValueOfSignal('NEW_JDD_OBC_DCDC_5B1','KILOMETRAGE_JDD',16777214,ConditionEnum.Equal,0,0,[],[])
    StartTime = dArrTimeStamp1[0]
    EndTime = dArrTimeStamp2[0]

    CursorPosition = [StartTime, EndTime]
    STLA_CAN.DBC.ExportWfmFile(['IFB_VersionInfo','IFB_Volt','IFB_Volt','IFB_Volt','SUPV_V2_OBC_DCDC_591','IFB_CC_CP','IFB_CC_CP',
                                'IFB_CC_CP','IFB_CC_CP','DYN_E_VCU_342','SUPV_V2_OBC_DCDC_591','NEW_JDD_OBC_DCDC_5B1'],
                                ['IFB_V_VerInfo6or13or20','IFB_Volt_KL30','IFB_Volt_KL15','IFB_Volt_LVCC','RCD_LINE_STATE',
                                 'IFB_CCCP_CC_Res','IFB_CCCP_CP_Volt','IFB_CCCP_CP_Fre','IFB_CCCP_CP_Duty','REVEIL_PRINCIPAL',
                                 'ECU_ELEC_STATE_RCD','KILOMETRAGE_JDD'],
                                ''
    )
    Sleep(2000)
    STLA_CAN.DBC.ConfigureCursor(CursorEnum.X,CursorPosition)
    STLA_CAN.DBC.ExportImage(ImageFormatEnum.PNG,ColorInversionEnum.ON,'')

    # print(f" 前置步骤结果：{PreCondition}, 测试步骤1结果: {TestResult1}")
    TestResult = True if PreCondition and TestResult1  else False
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
