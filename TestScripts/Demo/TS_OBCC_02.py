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
    STLA_CAN.DBC.ConfigureSetting('EVTECH_STLA-M_TS-VF-2', 'TS-OBCC-02', RecordFileType.BLF, None)
    STLA_CAN.DBC.SetChannel('All', ['ALL'], RecordEnum.ON)
    STLA_CAN.DBC.RecordState(AcqEnum.Start)
    InitAllCANMessage()
    STLA_CAN.DBC.SetSignal(1, 'DYN_E_VCU_342', 'REVEIL_PRINCIPAL', 2)

    低压辅源.SCPI.Write(':SOUR1:VOLT 12.5;:SOUR1:CURR 3;:OUTP CH1,ON')
    低压辅源.SCPI.Write(':SOUR2:VOLT 5;:SOUR2:CURR 3;:OUTP CH2,ON')
    电阻控制板.Modbus.SetRegister(iID=1,Reg=3072,Data='220')
    信号发生器.SCPI.Write(':SOUR1:APPL:SQU 1000,12.1,0,0;:SOUR1:FUNC:SQU:DCYC 80;:OUTP1 ON')
    Sleep(1000)

    交流源载一体机.Set.Basic(ACPwrModeEnum.SOUR, ACChannelEnum.SING, ACCouplingEnum.AC,0, ACPwrWorkModeEnum.CC)
    交流源载一体机.Set.Freq(dFreq=50)
    交流源载一体机.Set.Volt(dealListData([230.0, 0.0, 0.0]),dealListData([0.0, 0.0, 0.0]))
    高压源载一体机.Set.Basic(DCPwrModeEnum.NORM, DCPwrWorkModeEnum.NONE)
    高压源载一体机.Set.Volt(dVolt=365)
    交流源载一体机.Out.Enable(ACeEnable.ON)
    高压源载一体机.Out.Enable(eEnable.ON)
    Sleep(500)

    STLA_CAN.DBC.SetSignal(1,'DAT_E_VCU_448','CABLE_LOCK_REQ',1)
    Sleep(500)

    StartTime = TimeStamp()     # 获取毫秒级时间戳
    Test, OBCFaultState = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_421','OBC_FAULT_STATE', 0.0)
    Test, AcdcConversionState = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_501','ACDC_CONVERSION_STATE', 0.0)
    Test, EvsePlugLockState = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_421','EVSE_PLUG_LOCK_STATE', 0.0)
    print(f"OBC故障等级:{OBCFaultState}, OBC状态: {AcdcConversionState}, 电子锁状态: {EvsePlugLockState}")
    PreTestResult1 = OBCFaultState == 0
    PreTestResult2 = EvsePlugLockState == 1
    PreCondition = True if PreTestResult1 and PreTestResult2 else False
    TestResult1 = True if AcdcConversionState == 0 else False

    list = []
    SetOBCACOutputVoltage = 0
    for i in range(100):
        高压源载一体机.Set.Volt(dVolt=SetOBCACOutputVoltage)
        Sleep(1500)

        if SetOBCACOutputVoltage <= 20:
            Test, ReadOBCHVVoltage = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_541','DCDC_REAL_HV_VOLT_HD', 0.0)
            print(f"设置OBC输出电压:{SetOBCACOutputVoltage}V, DCDC_REAL_HV_VOLT_HD: {ReadOBCHVVoltage}")
            SingleResult = ReadOBCHVVoltage == 0
            if SingleResult == True:
                list.append(True)
            else:
                list.append(False)
        else:
            Test, ReadOBCHVVoltage = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_541','DCDC_REAL_HV_VOLT_HD', 0.0)
            print(f"设置OBC输出电压:{SetOBCACOutputVoltage}V, DCDC_REAL_HV_VOLT_HD: {ReadOBCHVVoltage}")
            SingleResult = (ReadOBCHVVoltage<=SetOBCACOutputVoltage*1.10) and (ReadOBCHVVoltage>=SetOBCACOutputVoltage*0.90)
            if SingleResult == True:
                list.append(True)
            else:
                list.append(False)

        SetOBCACOutputVoltage += 25

        if SetOBCACOutputVoltage >= 400:
            EndTime = TimeStamp()       # 获取毫秒级时间戳
            TestResult2 = min(list)
            print(list)
            break

    CloseAllCANMessage()
    CloseAllDevice()
    STLA_CAN.DBC.RecordState(AcqEnum.Stop)

    print(f"前置条件结果:{PreCondition}, 测试步骤1结果: {TestResult1}, 测试步骤2结果: {TestResult2}")
    TestResult = True if PreCondition and TestResult1 and TestResult2 else False
    if TestResult == True:
        TestResultDisplay = '合格'
        print(TestResultDisplay)
    else:
        TestResultDisplay = '不合格'
        print(TestResultDisplay)
    
