from CommonFunction.FunctionClass_V2 import *
from UtilityClass.UtilityClass01_DeviceConnectInit import *
# from UtilityClass.UtilityClass02_TSCANConnectInit import *
from CommonFunction.Common00_Fuction import *
from CommonFunction.Common01_InitDevice import InitDevice
from CommonFunction.Common01_CloseDevice import CloseAllDevice
from CommonFunction.Common02_InitCANMessage import InitAllCANMessage
from CommonFunction.Common03_CloseCANMessage import CloseAllCANMessage

if __name__ == '__main__':

    InitDevice()
    Sleep(1000)
    STLA_CAN.DBC.ConfigureSetting('EVTECH_STLA-M_TS-VF-2', 'TS_DCC_02', RecordFileType.BLF, None)
    STLA_CAN.DBC.SetChannel('All', ['ALL'], RecordEnum.ON)
    STLA_CAN.DBC.RecordState(AcqEnum.Start)
    InitAllCANMessage()
    STLA_CAN.DBC.SetSignal(1, 'DYN_E_VCU_342', 'REVEIL_PRINCIPAL', 2)

    低压辅源.SCPI.Write(':SOUR1:VOLT 12.5;:SOUR1:CURR 3;:OUTP CH1,ON')
    低压辅源.SCPI.Write(':SOUR2:VOLT 5;:SOUR2:CURR 3;:OUTP CH2,ON')
    Sleep(2500)

    高压源载一体机.Set.Volt(dVolt=375)
    高压源载一体机.Out.Enable(eEnable.ON)
    Sleep(1000)

    STLA_CAN.DBC.SetMessage(1,'DYN_E_VCU_342',['0','0','0','15','0','0','0','0','0'])
    STLA_CAN.DBC.Trigger(1, 'DYN_E_VCU_342', True)
    Sleep(1000)
    Test , DCDCStateBB1 = STLA_CAN.DBC.GetSignal(1, 'DAT_OBC_DCDC_541', 'DCDC_STATE_BB', 0.0)
    PreCondition = True if DCDCStateBB1 == 2 else False

    STLA_CAN.DBC.SetSignal(1, 'DAT_E_VCU_448', 'REG_MODE_DCDC_BB_REQ', 1)
    Sleep(1000)
    Test , DCDCStateBB2 = STLA_CAN.DBC.GetSignal(1, 'DAT_OBC_DCDC_541', 'DCDC_STATE_BB', 0.0)
    Test , DCDCConvLvVoltHD1 = STLA_CAN.DBC.GetSignal(1, 'DAT_OBC_DCDC_281', 'DCDC_CONV_LV_VOLT_HD', 0.0)
    TestResult1 = DCDCStateBB2 == 3
    print("DCDC_CONV_LV_VOLT_HD电压为: ",DCDCConvLvVoltHD1)
    TestResult2 = DCDCConvLvVoltHD1 >= 14.7 and DCDCConvLvVoltHD1 <= 15.3

    STLA_CAN.DBC.Trigger(1, 'DYN_E_VCU_342', False)
    Sleep(10000)
    Test , DCDCConvLvVoltHD2 = STLA_CAN.DBC.GetSignal(1, 'DAT_OBC_DCDC_281', 'DCDC_CONV_LV_VOLT_HD', 0.0)
    TestResult3 = DCDCConvLvVoltHD2 >=0 and DCDCConvLvVoltHD2 <= 5
    Sleep(2000)

    CloseAllCANMessage()
    CloseAllDevice()
    STLA_CAN.DBC.RecordState(AcqEnum.Stop)

    print(f"前置条件结果:{PreCondition}, 测试步骤1结果: {TestResult1}, 测试步骤2结果: {TestResult2}, 测试步骤3结果: {TestResult3}")
    TestResult = True if PreCondition and TestResult1 and TestResult2 and TestResult3 else False
    if TestResult == True:
        TestResultDisplay = '合格'
        print(TestResultDisplay)
    else:
        TestResultDisplay = '不合格'
        print(TestResultDisplay)