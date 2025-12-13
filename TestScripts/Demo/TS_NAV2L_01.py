from CommonFuction.FunctionClass_V2 import *
from UtilityClass.UtilityClass01_DeviceConnectInit import *
# from UtilityClass.UtilityClass02_TSCANConnectInit import *
from CommonFuction.Common00_Fuction import *
from CommonFuction.Common01_InitDevice import InitDevice
from CommonFuction.Common01_CloseDevice import CloseAllDevice
from CommonFuction.Common02_InitCANMessage import InitAllCANMessage
from CommonFuction.Common03_CloseCANMessage import CloseAllCANMessage

if __name__ == '__main__':
    
    InitDevice()
    Sleep(1000)
    Log4NetWrapper.InitLogManage("EVTECH_STLA-M_TS-VF-2", "TS-NAV2L-01")
    STLA_CAN.DBC.ConfigureSetting('EVTECH_STLA-M_TS-VF-2', 'TS-NAV2L-01', RecordFileType.BLF, None)
    STLA_CAN.DBC.SetChannel('All', ['ALL'], RecordEnum.ON)
    STLA_CAN.DBC.RecordState(AcqEnum.Start)
    InitAllCANMessage()

    低压辅源.SCPI.Write(':SOUR1:VOLT 12.5;:SOUR1:CURR 3;:OUTP CH1,ON')
    低压辅源.SCPI.Write(':SOUR2:VOLT 5;:SOUR2:CURR 3;:OUTP CH2,ON')
    低压辅源.SCPI.Write(':SOUR3:VOLT 0.6;:SOUR3:CURR 3;:OUTP CH3,ON')
    电阻控制板.Modbus.SetRegister(iID=1,Reg=3072,Data='150')
    信号发生器.SCPI.Write(':SOUR1:APPL:SQU 125,12.1,0,0;:SOUR1:FUNC:SQU:DCYC 53;:OUTP1 ON')
    Sleep(2000)

    Test , ObcChrgConnConf = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_421','OBC_CHRG_CONN_CONF', 0.0)
    PreTestResult1 = ObcChrgConnConf == 2

    STLA_CAN.DBC.SetSignal(1,'DAT_TBMU_314', 'MIN_ALLOW_DISCHRG_VOLTAGE', 100)
    STLA_CAN.DBC.SetSignal(1,'DAT_E_VCU_448','OBC_EVSE_REQUEST',1)
    STLA_CAN.DBC.SetSignal(1,'DAT_E_VCU_448','CABLE_LOCK_REQ',1)
    Sleep(1000)

    StartTime = TimeStamp()     # 获取毫秒级时间戳
    Test , OBCFaultState = STLA_CAN.DBC.GetSignal(1, 'DAT_OBC_DCDC_421', 'OBC_FAULT_STATE', 0.0)
    Test , EvsePlugLockState = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_421','EVSE_PLUG_LOCK_STATE', 0.0)
    Test , AcChargeModeAvail1 = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_501','AC_CHARGE_MODE_AVAIL', 0.0)
    PreTestResult2 = OBCFaultState <= 1
    PreTestResult3 = EvsePlugLockState == 1
    PreTestResult4 = AcChargeModeAvail1 == 0
    PreCondition = True if PreTestResult1 and PreTestResult2 and PreTestResult3 and PreTestResult4 else False
    Log4NetWrapper.WriteToOutput(f'OBC_FAULT_STATE:{OBCFaultState},EVSE_PLUG_LOCK_STATE:{EvsePlugLockState},AC_CHARGE_MODE_AVAIL:{AcChargeModeAvail1}')
    Log4NetWrapper.WriteToOutput(f'PreCondition:{PreCondition},PreTestResult1:{PreTestResult1},PreTestResult2:{PreTestResult2},PreTestResult3:{PreTestResult3},PreTestResult4:{PreTestResult4}')
    print(PreTestResult1,PreTestResult2,PreTestResult3,PreTestResult4)
    Sleep(2000)

    交流源载一体机.Set.Basic(ACPwrModeEnum.LOAD, ACChannelEnum.SING, ACCouplingEnum.AC,0, ACPwrWorkModeEnum.CR)
    高压源载一体机.Set.Basic(DCPwrModeEnum.NORM, DCPwrWorkModeEnum.NONE)
    高压源载一体机.Set.Volt(dVolt=350)
    高压源载一体机.Out.Enable(eEnable.ON)
    Sleep(1000)

    STLA_CAN.DBC.SetSignal(1,'DAT_E_VCU_448','ACDC_CONVERSION_REQUEST',3)
    Sleep(2000)

    EndTime = TimeStamp()       # 获取毫秒级时间戳
    Test , AcChargeModeAvail2 = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_501','AC_CHARGE_MODE_AVAIL', 0.0)
    Test , DcChargeModeAvail2 = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_501','DC_CHARGE_MODE_AVAIL', 0.0)
    Test , BidirV2lAvail2 = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_501','BIDIR_V2L_AVAIL', 0.0)
    Test , ObcEvseMesAcVoltage2 = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_441','OBC_EVSE_MES_AC_VOLTAGE', 0.0)
    TestResult11=AcChargeModeAvail2==0
    TestResult12=DcChargeModeAvail2==0
    TestResult13=BidirV2lAvail2==1
    TestResult14=(ObcEvseMesAcVoltage2>=120*0.9) and (ObcEvseMesAcVoltage2<=120*1.1)
    TestResult1 = True if TestResult11 and TestResult12 and TestResult13 and TestResult14 else False
    Log4NetWrapper.WriteToOutput(f'AC_CHARGE_MODE_AVAIL:{AcChargeModeAvail2},DC_CHARGE_MODE_AVAIL:{DcChargeModeAvail2},BIDIR_V2L_AVAIL:{BidirV2lAvail2},OBC_EVSE_MES_AC_VOLTAGE:{ObcEvseMesAcVoltage2}')
    Log4NetWrapper.WriteToOutput(f'TestResult1:{TestResult1},TestResult11:{TestResult11},TestResult12:{TestResult12},TestResult13:{TestResult13},TestResult14:{TestResult14}')
    print(TestResult11,TestResult12,TestResult13,TestResult14)
    Sleep(2000)

    CloseAllCANMessage()
    CloseAllDevice()
    STLA_CAN.DBC.RecordState(AcqEnum.Stop)

    Test, dArrTimeStamp1, dArrTimeStampList1= STLA_CAN.DBC.FindValueOfSignal('DAT_E_VCU_448','ACDC_CONVERSION_REQUEST',3,ConditionEnum.Equal,0,0,[],[])
    Test, dArrTimeStamp2, dArrTimeStampList2= STLA_CAN.DBC.FindValueOfSignal('DAT_OBC_DCDC_441','OBC_EVSE_MES_AC_VOLTAGE',110,ConditionEnum.Morethan,0,0,[],[])
    StartTime = dArrTimeStamp1[0]
    EndTime = dArrTimeStamp2[0]
    CursorPosition = [StartTime, EndTime]
    TestResult2 = EndTime - StartTime <= 1000
    Log4NetWrapper.WriteToOutput(f'StartTime:{StartTime},EndTime:{EndTime},CursorPosition:{CursorPosition}')
    Log4NetWrapper.WriteToOutput(f'TestResult2:{TestResult2}')
    
    STLA_CAN.DBC.ExportWfmFile(['DAT_OBC_DCDC_441','DAT_OBC_DCDC_501','DAT_OBC_DCDC_501','DAT_OBC_DCDC_421','DAT_OBC_DCDC_421',
                                'DAT_OBC_DCDC_501','DAT_OBC_DCDC_501','DAT_E_VCU_448','DAT_OBC_DCDC_421','IFB_CC_CP'],
                               ['OBC_EVSE_MES_AC_VOLTAGE','DC_CHARGE_MODE_AVAIL','BIDIR_V2L_AVAIL','OBC_FAULT_STATE',
                                'OBC_CHRG_CONN_CONF','AC_CHARGE_MODE_AVAIL','ACDC_CONVERSION_STATE','CABLE_LOCK_REQ',
                                'EVSE_PLUG_LOCK_STATE','IFB_CCCP_CP_Fre'],
                                ''
    )
    Sleep(2000)
    STLA_CAN.DBC.ConfigureCursor(CursorEnum.X,CursorPosition)
    STLA_CAN.DBC.ExportImage(ImageFormatEnum.PNG,ColorInversionEnum.ON,'')

    print(f"前置条件结果:{PreCondition}, 测试步骤1结果: {TestResult1}, 测试步骤2结果: {TestResult2},时间戳: {CursorPosition}")
    TestResult = True if PreCondition and TestResult1 and TestResult2 else False
    if TestResult == True:
        TestResultDisplay = '合格'
        Log4NetWrapper.WriteToOutput(f'测试结果:{TestResultDisplay}')
        print(TestResultDisplay)
    else:
        TestResultDisplay = '不合格'
        Log4NetWrapper.WriteToOutput(f'测试结果:{TestResultDisplay}')
        print(TestResultDisplay)
    Log4NetWrapper.WriteToOutput(f'$Report:Test result:{TestResultDisplay}#,$Actual test result:OBC_FAULT_STATE{OBCFaultState},EVSE_PLUG_LOCK_STATE:{EvsePlugLockState}, AC_CHARGE_MODE_AVAIL:{AcChargeModeAvail1},AC_CHARGE_MODE_AVAIL:{AcChargeModeAvail2},BIDIR_V2L_AVAIL:{BidirV2lAvail2},OBC_EVSE_MES_AC_VOLTAGE:{ObcEvseMesAcVoltage2}#')
