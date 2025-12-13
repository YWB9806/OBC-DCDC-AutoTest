from CommonFuction.FunctionClass_V2 import *
from UtilityClass.UtilityClass01_DeviceConnectInit import *
# from UtilityClass.UtilityClass02_TSCANConnectInit import *
from CommonFuction.Common00_Fuction import *
from CommonFuction.Common01_InitDevice import InitDevice
from CommonFuction.Common01_CloseDevice import CloseAllDevice
from CommonFuction.Common02_InitCANMessage import InitAllCANMessage
from CommonFuction.Common03_CloseCANMessage import CloseAllCANMessage

if __name__ == '__main__':

    StartTestMethodTotal = [True,True,True,True,True,True,True,True]
    StartTestMethod1=StartTestMethodTotal[0]
    StartTestMethod2=StartTestMethodTotal[1]
    StartTestMethod3=StartTestMethodTotal[2]
    StartTestMethod4=StartTestMethodTotal[3]
    StartTestMethod5=StartTestMethodTotal[4]
    StartTestMethod6=StartTestMethodTotal[5]
    StartTestMethod7=StartTestMethodTotal[6]
    StartTestMethod8=StartTestMethodTotal[7]

    if StartTestMethod1 == True:
        CloseAllCANMessage()
        InitDevice()
        Sleep(1000)
        STLA_CAN.DBC.ConfigureSetting('EVTECH_STLA-M_TS-VF-2', 'TS-NAV2L-05-1', RecordFileType.BLF, None)
        STLA_CAN.DBC.SetChannel('All', ['ALL'], RecordEnum.ON)
        STLA_CAN.DBC.RecordState(AcqEnum.Start)
        InitAllCANMessage()

        低压辅源.SCPI.Write(':SOUR1:VOLT 12.5;:SOUR1:CURR 3;:OUTP CH1,ON')
        低压辅源.SCPI.Write(':SOUR2:VOLT 5;:SOUR2:CURR 3;:OUTP CH2,ON')
        电阻控制板.Modbus.SetRegister(iID=1,Reg=3072,Data='150')
        信号发生器.SCPI.Write(':SOUR1:APPL:SQU 125,12.1,0,0;:SOUR1:FUNC:SQU:DCYC 53;:OUTP1 ON')
        Sleep(2000)

        STLA_CAN.DBC.SetSignal(1, 'DAT_TBMU_314', 'MIN_ALLOW_DISCHRG_VOLTAGE', 100)
        STLA_CAN.DBC.SetSignal(1,'DAT_E_VCU_448','OBC_EVSE_REQUEST',1)
        STLA_CAN.DBC.SetSignal(1,'DAT_E_VCU_448','CABLE_LOCK_REQ',1)
        Sleep(3000)

        交流源载一体机.Set.Basic(ACPwrModeEnum.LOAD, ACChannelEnum.SING, ACCouplingEnum.AC,0, ACPwrWorkModeEnum.CR)
        高压源载一体机.Set.Basic(DCPwrModeEnum.NORM, DCPwrWorkModeEnum.NONE)
        高压源载一体机.Set.Volt(dVolt=350)
        高压源载一体机.Out.Enable(eEnable.ON)
        Sleep(1000)

        STLA_CAN.DBC.SetSignal(1,'DAT_E_VCU_448','ACDC_CONVERSION_REQUEST',3)
        Sleep(2000)

        StartTime = TimeStamp()     # 获取毫秒级时间戳
        Test , ACDCConversionState0 = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_501','ACDC_CONVERSION_STATE', 0.0)
        PreCondition = ACDCConversionState0 == 4
        Sleep(2000)

        电阻控制板.Modbus.SetRegister(iID=1,Reg=3072,Data='240')
        Sleep(1000)

        EndTime = TimeStamp()       # 获取毫秒级时间戳
        Test , ObcChrgConnConf1 = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_421','OBC_CHRG_CONN_CONF', 0.0)
        Test , BidirV2LAvail1 = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_501','BIDIR_V2L_AVAIL', 0.0)
        Test , ACDCConversionState1 = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_501','ACDC_CONVERSION_STATE', 0.0)
        TestResult11 = ObcChrgConnConf1 == 1
        TestResult12 = BidirV2LAvail1 == 0
        TestResult13 = ACDCConversionState1 == 0
        TestResult1 = True if TestResult11 and TestResult12 and TestResult13 else False
        print(TestResult11,TestResult12,TestResult13)
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

        print(f"前置条件结果:{PreCondition}, 测试步骤1结果: {TestResult1}, 测试步骤2结果: {TestResult2},时间戳: {CursorPosition}")
        TestResult = True if PreCondition and TestResult1 and TestResult2 else False
        if TestResult == True:
            TestResultDisplay = '合格'
            print(TestResultDisplay)
        else:
            TestResultDisplay = '不合格'
            print(TestResultDisplay)

    if StartTestMethod2 == True:
        CloseAllCANMessage()
        InitDevice()
        Sleep(1000)
        STLA_CAN.DBC.ConfigureSetting('EVTECH_STLA-M_TS-VF-2', 'TS-NAV2L-05-2', RecordFileType.BLF, None)
        STLA_CAN.DBC.SetChannel('All', ['ALL'], RecordEnum.ON)
        STLA_CAN.DBC.RecordState(AcqEnum.Start)
        InitAllCANMessage()

        低压辅源.SCPI.Write(':SOUR1:VOLT 12.5;:SOUR1:CURR 3;:OUTP CH1,ON')
        低压辅源.SCPI.Write(':SOUR2:VOLT 5;:SOUR2:CURR 3;:OUTP CH2,ON')
        电阻控制板.Modbus.SetRegister(iID=1,Reg=3072,Data='150')
        信号发生器.SCPI.Write(':SOUR1:APPL:SQU 125,12.1,0,0;:SOUR1:FUNC:SQU:DCYC 53;:OUTP1 ON')
        Sleep(2000)

        STLA_CAN.DBC.SetSignal(1, 'DAT_TBMU_314', 'MIN_ALLOW_DISCHRG_VOLTAGE', 100)
        STLA_CAN.DBC.SetSignal(1,'DAT_E_VCU_448','OBC_EVSE_REQUEST',1)
        STLA_CAN.DBC.SetSignal(1,'DAT_E_VCU_448','CABLE_LOCK_REQ',1)
        Sleep(3000)

        交流源载一体机.Set.Basic(ACPwrModeEnum.LOAD, ACChannelEnum.SING, ACCouplingEnum.AC,0, ACPwrWorkModeEnum.CR)
        高压源载一体机.Set.Basic(DCPwrModeEnum.NORM, DCPwrWorkModeEnum.NONE)
        高压源载一体机.Set.Volt(dVolt=350)
        高压源载一体机.Out.Enable(eEnable.ON)
        Sleep(1000)

        STLA_CAN.DBC.SetSignal(1,'DAT_E_VCU_448','ACDC_CONVERSION_REQUEST',3)
        Sleep(2000)

        StartTime = TimeStamp()     # 获取毫秒级时间戳
        Test , ACDCConversionState0 = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_501','ACDC_CONVERSION_STATE', 0.0)
        PreCondition = ACDCConversionState0 == 4
        Sleep(2000)

        电阻控制板.Modbus.SetRegister(iID=1,Reg=3072,Data='3500')
        Sleep(1000)

        EndTime = TimeStamp()       # 获取毫秒级时间戳
        Test , ObcChrgConnConf1 = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_421','OBC_CHRG_CONN_CONF', 0.0)
        Test , BidirV2LAvail1 = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_501','BIDIR_V2L_AVAIL', 0.0)
        Test , ACDCConversionState1 = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_501','ACDC_CONVERSION_STATE', 0.0)
        TestResult11 = ObcChrgConnConf1 == 3
        TestResult12 = BidirV2LAvail1 == 0
        TestResult13 = ACDCConversionState1 == 0
        TestResult1 = True if TestResult11 and TestResult12 and TestResult13 else False
        print(TestResult11,TestResult12,TestResult13)
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

        print(f"前置条件结果:{PreCondition}, 测试步骤1结果: {TestResult1}, 测试步骤2结果: {TestResult2},时间戳: {CursorPosition}")
        TestResult = True if PreCondition and TestResult1 and TestResult2 else False
        if TestResult == True:
            TestResultDisplay = '合格'
            print(TestResultDisplay)
        else:
            TestResultDisplay = '不合格'
            print(TestResultDisplay)

    if StartTestMethod3 == True:
        CloseAllCANMessage()
        InitDevice()
        Sleep(1000)
        STLA_CAN.DBC.ConfigureSetting('EVTECH_STLA-M_TS-VF-2', 'TS-NAV2L-05-3', RecordFileType.BLF, None)
        STLA_CAN.DBC.SetChannel('All', ['ALL'], RecordEnum.ON)
        STLA_CAN.DBC.RecordState(AcqEnum.Start)
        InitAllCANMessage()

        低压辅源.SCPI.Write(':SOUR1:VOLT 12.5;:SOUR1:CURR 3;:OUTP CH1,ON')
        低压辅源.SCPI.Write(':SOUR2:VOLT 5;:SOUR2:CURR 3;:OUTP CH2,ON')
        电阻控制板.Modbus.SetRegister(iID=1,Reg=3072,Data='150')
        信号发生器.SCPI.Write(':SOUR1:APPL:SQU 125,12.1,0,0;:SOUR1:FUNC:SQU:DCYC 53;:OUTP1 ON')
        Sleep(2000)

        STLA_CAN.DBC.SetSignal(1, 'DAT_TBMU_314', 'MIN_ALLOW_DISCHRG_VOLTAGE', 100)
        STLA_CAN.DBC.SetSignal(1,'DAT_E_VCU_448','OBC_EVSE_REQUEST',1)
        STLA_CAN.DBC.SetSignal(1,'DAT_E_VCU_448','CABLE_LOCK_REQ',1)
        Sleep(3000)

        交流源载一体机.Set.Basic(ACPwrModeEnum.LOAD, ACChannelEnum.SING, ACCouplingEnum.AC,0, ACPwrWorkModeEnum.CR)
        高压源载一体机.Set.Basic(DCPwrModeEnum.NORM, DCPwrWorkModeEnum.NONE)
        高压源载一体机.Set.Volt(dVolt=350)
        高压源载一体机.Out.Enable(eEnable.ON)
        Sleep(1000)

        STLA_CAN.DBC.SetSignal(1,'DAT_E_VCU_448','ACDC_CONVERSION_REQUEST',3)
        Sleep(2000)

        StartTime = TimeStamp()     # 获取毫秒级时间戳
        Test , ACDCConversionState0 = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_501','ACDC_CONVERSION_STATE', 0.0)
        PreCondition = ACDCConversionState0 == 4
        Sleep(2000)

        STLA_CAN.DBC.SetSignal(1,'DAT_E_VCU_448','ACDC_CONVERSION_REQUEST',0)
        Sleep(1000)

        EndTime = TimeStamp()       # 获取毫秒级时间戳
        Test , BidirV2LAvail1 = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_501','BIDIR_V2L_AVAIL', 0.0)
        Test , ACDCConversionState1 = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_501','ACDC_CONVERSION_STATE', 0.0)
        TestResult11 = BidirV2LAvail1 == 0
        TestResult12 = ACDCConversionState1 == 0
        TestResult1 = True if TestResult11 and TestResult12 else False
        print(TestResult11,TestResult12)
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

        print(f"前置条件结果:{PreCondition}, 测试步骤1结果: {TestResult1}, 测试步骤2结果: {TestResult2},时间戳: {CursorPosition}")
        TestResult = True if PreCondition and TestResult1 and TestResult2 else False
        if TestResult == True:
            TestResultDisplay = '合格'
            print(TestResultDisplay)
        else:
            TestResultDisplay = '不合格'
            print(TestResultDisplay)

    if StartTestMethod4 == True:
        CloseAllCANMessage()
        InitDevice()
        Sleep(1000)
        STLA_CAN.DBC.ConfigureSetting('EVTECH_STLA-M_TS-VF-2', 'TS-NAV2L-05-4', RecordFileType.BLF, None)
        STLA_CAN.DBC.SetChannel('All', ['ALL'], RecordEnum.ON)
        STLA_CAN.DBC.RecordState(AcqEnum.Start)
        InitAllCANMessage()

        低压辅源.SCPI.Write(':SOUR1:VOLT 12.5;:SOUR1:CURR 3;:OUTP CH1,ON')
        低压辅源.SCPI.Write(':SOUR2:VOLT 5;:SOUR2:CURR 3;:OUTP CH2,ON')
        电阻控制板.Modbus.SetRegister(iID=1,Reg=3072,Data='150')
        信号发生器.SCPI.Write(':SOUR1:APPL:SQU 125,12.1,0,0;:SOUR1:FUNC:SQU:DCYC 53;:OUTP1 ON')
        Sleep(2000)

        STLA_CAN.DBC.SetSignal(1, 'DAT_TBMU_314', 'MIN_ALLOW_DISCHRG_VOLTAGE', 100)
        STLA_CAN.DBC.SetSignal(1,'DAT_E_VCU_448','OBC_EVSE_REQUEST',1)
        STLA_CAN.DBC.SetSignal(1,'DAT_E_VCU_448','CABLE_LOCK_REQ',1)
        Sleep(3000)

        交流源载一体机.Set.Basic(ACPwrModeEnum.LOAD, ACChannelEnum.SING, ACCouplingEnum.AC,0, ACPwrWorkModeEnum.CR)
        高压源载一体机.Set.Basic(DCPwrModeEnum.NORM, DCPwrWorkModeEnum.NONE)
        高压源载一体机.Set.Volt(dVolt=350)
        高压源载一体机.Out.Enable(eEnable.ON)
        Sleep(1000)

        STLA_CAN.DBC.SetSignal(1,'DAT_E_VCU_448','ACDC_CONVERSION_REQUEST',3)
        Sleep(2000)

        StartTime = TimeStamp()     # 获取毫秒级时间戳
        Test , ACDCConversionState0 = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_501','ACDC_CONVERSION_STATE', 0.0)
        PreCondition = ACDCConversionState0 == 4
        Sleep(2000)

        高压源载一体机.Set.Volt(dVolt=504)
        Sleep(1000)

        EndTime = TimeStamp()       # 获取毫秒级时间戳
        Test , BidirV2LAvail1 = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_501','BIDIR_V2L_AVAIL', 0.0)
        Test , ACDCConversionState1 = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_501','ACDC_CONVERSION_STATE', 0.0)
        Test , OBCFaultState1 = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_421','OBC_FAULT_STATE', 0.0)

        TestResult11 = BidirV2LAvail1 == 0
        TestResult12 = ACDCConversionState1 == 0
        TestResult13 = OBCFaultState1 >= 1
        TestResult1 = True if TestResult11 and TestResult12 and TestResult13 else False
        print(TestResult11,TestResult12,TestResult13)
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

        print(f"前置条件结果:{PreCondition}, 测试步骤1结果: {TestResult1}, 测试步骤2结果: {TestResult2},时间戳: {CursorPosition}")
        TestResult = True if PreCondition and TestResult1 and TestResult2 else False
        if TestResult == True:
            TestResultDisplay = '合格'
            print(TestResultDisplay)
        else:
            TestResultDisplay = '不合格'
            print(TestResultDisplay)

    if StartTestMethod5 == True:
        CloseAllCANMessage()
        InitDevice()
        Sleep(1000)
        STLA_CAN.DBC.ConfigureSetting('EVTECH_STLA-M_TS-VF-2', 'TS-NAV2L-05-5', RecordFileType.BLF, None)
        STLA_CAN.DBC.SetChannel('All', ['ALL'], RecordEnum.ON)
        STLA_CAN.DBC.RecordState(AcqEnum.Start)
        InitAllCANMessage()

        低压辅源.SCPI.Write(':SOUR1:VOLT 12.5;:SOUR1:CURR 3;:OUTP CH1,ON')
        低压辅源.SCPI.Write(':SOUR2:VOLT 5;:SOUR2:CURR 3;:OUTP CH2,ON')
        电阻控制板.Modbus.SetRegister(iID=1,Reg=3072,Data='150')
        信号发生器.SCPI.Write(':SOUR1:APPL:SQU 125,12.1,0,0;:SOUR1:FUNC:SQU:DCYC 53;:OUTP1 ON')
        Sleep(2000)

        STLA_CAN.DBC.SetSignal(1, 'DAT_TBMU_314', 'MIN_ALLOW_DISCHRG_VOLTAGE', 100)
        STLA_CAN.DBC.SetSignal(1,'DAT_E_VCU_448','OBC_EVSE_REQUEST',1)
        STLA_CAN.DBC.SetSignal(1,'DAT_E_VCU_448','CABLE_LOCK_REQ',1)
        Sleep(3000)

        交流源载一体机.Set.Basic(ACPwrModeEnum.LOAD, ACChannelEnum.SING, ACCouplingEnum.AC,0, ACPwrWorkModeEnum.CR)
        高压源载一体机.Set.Basic(DCPwrModeEnum.NORM, DCPwrWorkModeEnum.NONE)
        高压源载一体机.Set.Volt(dVolt=350)
        高压源载一体机.Out.Enable(eEnable.ON)
        Sleep(1000)

        STLA_CAN.DBC.SetSignal(1,'DAT_E_VCU_448','ACDC_CONVERSION_REQUEST',3)
        Sleep(2000)

        StartTime = TimeStamp()     # 获取毫秒级时间戳
        Test , ACDCConversionState0 = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_501','ACDC_CONVERSION_STATE', 0.0)
        PreCondition = ACDCConversionState0 == 4
        Sleep(2000)

        STLA_CAN.DBC.SetSignal(1,'DAT_E_VCU_448','OBC_EVSE_REQUEST',10)
        Sleep(1000)

        EndTime = TimeStamp()       # 获取毫秒级时间戳
        Test , BidirV2LAvail1 = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_501','BIDIR_V2L_AVAIL', 0.0)
        Test , ACDCConversionState1 = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_501','ACDC_CONVERSION_STATE', 0.0)
        TestResult11 = BidirV2LAvail1 == 0
        TestResult12 = ACDCConversionState1 == 0
        TestResult1 = True if TestResult11 and TestResult12 else False
        print(TestResult11,TestResult12)
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

        print(f"前置条件结果:{PreCondition}, 测试步骤1结果: {TestResult1}, 测试步骤2结果: {TestResult2},时间戳: {CursorPosition}")
        TestResult = True if PreCondition and TestResult1 and TestResult2 else False
        if TestResult == True:
            TestResultDisplay = '合格'
            print(TestResultDisplay)
        else:
            TestResultDisplay = '不合格'
            print(TestResultDisplay)

    if StartTestMethod6 == True:
        CloseAllCANMessage()
        InitDevice()
        Sleep(1000)
        STLA_CAN.DBC.ConfigureSetting('EVTECH_STLA-M_TS-VF-2', 'TS-NAV2L-05-6', RecordFileType.BLF, None)
        STLA_CAN.DBC.SetChannel('All', ['ALL'], RecordEnum.ON)
        STLA_CAN.DBC.RecordState(AcqEnum.Start)
        InitAllCANMessage()

        低压辅源.SCPI.Write(':SOUR1:VOLT 12.5;:SOUR1:CURR 3;:OUTP CH1,ON')
        低压辅源.SCPI.Write(':SOUR2:VOLT 5;:SOUR2:CURR 3;:OUTP CH2,ON')
        电阻控制板.Modbus.SetRegister(iID=1,Reg=3072,Data='150')
        信号发生器.SCPI.Write(':SOUR1:APPL:SQU 125,12.1,0,0;:SOUR1:FUNC:SQU:DCYC 53;:OUTP1 ON')
        Sleep(2000)

        STLA_CAN.DBC.SetSignal(1, 'DAT_TBMU_314', 'MIN_ALLOW_DISCHRG_VOLTAGE', 100)
        STLA_CAN.DBC.SetSignal(1,'DAT_E_VCU_448','OBC_EVSE_REQUEST',1)
        STLA_CAN.DBC.SetSignal(1,'DAT_E_VCU_448','CABLE_LOCK_REQ',1)
        Sleep(3000)

        交流源载一体机.Set.Basic(ACPwrModeEnum.LOAD, ACChannelEnum.SING, ACCouplingEnum.AC,0, ACPwrWorkModeEnum.CR)
        高压源载一体机.Set.Basic(DCPwrModeEnum.NORM, DCPwrWorkModeEnum.NONE)
        高压源载一体机.Set.Volt(dVolt=350)
        高压源载一体机.Out.Enable(eEnable.ON)
        Sleep(1000)

        STLA_CAN.DBC.SetSignal(1,'DAT_E_VCU_448','ACDC_CONVERSION_REQUEST',3)
        Sleep(2000)

        StartTime = TimeStamp()     # 获取毫秒级时间戳
        Test , ACDCConversionState0 = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_501','ACDC_CONVERSION_STATE', 0.0)
        PreCondition = ACDCConversionState0 == 4
        Sleep(2000)

        高压源载一体机.Set.Volt(dVolt=90)
        Sleep(1000)

        EndTime = TimeStamp()       # 获取毫秒级时间戳
        Test , BidirV2LAvail1 = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_501','BIDIR_V2L_AVAIL', 0.0)
        Test , ACDCConversionState1 = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_501','ACDC_CONVERSION_STATE', 0.0)
        TestResult11 = BidirV2LAvail1 == 0
        TestResult12 = ACDCConversionState1 == 0
        TestResult1 = True if TestResult11 and TestResult12 else False
        print(TestResult11,TestResult12)
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

        print(f"前置条件结果:{PreCondition}, 测试步骤1结果: {TestResult1}, 测试步骤2结果: {TestResult2},时间戳: {CursorPosition}")
        TestResult = True if PreCondition and TestResult1 and TestResult2 else False
        if TestResult == True:
            TestResultDisplay = '合格'
            print(TestResultDisplay)
        else:
            TestResultDisplay = '不合格'
            print(TestResultDisplay)

    if StartTestMethod7 == True:
        CloseAllCANMessage()
        InitDevice()
        Sleep(1000)
        STLA_CAN.DBC.ConfigureSetting('EVTECH_STLA-M_TS-VF-2', 'TS-NAV2L-05-7', RecordFileType.BLF, None)
        STLA_CAN.DBC.SetChannel('All', ['ALL'], RecordEnum.ON)
        STLA_CAN.DBC.RecordState(AcqEnum.Start)
        InitAllCANMessage()

        低压辅源.SCPI.Write(':SOUR1:VOLT 12.5;:SOUR1:CURR 3;:OUTP CH1,ON')
        低压辅源.SCPI.Write(':SOUR2:VOLT 5;:SOUR2:CURR 3;:OUTP CH2,ON')
        电阻控制板.Modbus.SetRegister(iID=1,Reg=3072,Data='150')
        信号发生器.SCPI.Write(':SOUR1:APPL:SQU 125,12.1,0,0;:SOUR1:FUNC:SQU:DCYC 53;:OUTP1 ON')
        Sleep(2000)

        STLA_CAN.DBC.SetSignal(1, 'DAT_TBMU_314', 'MIN_ALLOW_DISCHRG_VOLTAGE', 100)
        STLA_CAN.DBC.SetSignal(1,'DAT_E_VCU_448','OBC_EVSE_REQUEST',1)
        STLA_CAN.DBC.SetSignal(1,'DAT_E_VCU_448','CABLE_LOCK_REQ',1)
        Sleep(3000)

        交流源载一体机.Set.Basic(ACPwrModeEnum.LOAD, ACChannelEnum.SING, ACCouplingEnum.AC,0, ACPwrWorkModeEnum.CR)
        高压源载一体机.Set.Basic(DCPwrModeEnum.NORM, DCPwrWorkModeEnum.NONE)
        高压源载一体机.Set.Volt(dVolt=350)
        高压源载一体机.Out.Enable(eEnable.ON)
        Sleep(1000)

        STLA_CAN.DBC.SetSignal(1,'DAT_E_VCU_448','ACDC_CONVERSION_REQUEST',3)
        Sleep(2000)

        StartTime = TimeStamp()     # 获取毫秒级时间戳
        Test , ACDCConversionState0 = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_501','ACDC_CONVERSION_STATE', 0.0)
        PreCondition = ACDCConversionState0 == 4
        Sleep(2000)

        STLA_CAN.DBC.SetSignal(1,'DAT_E_VCU_448','CABLE_LOCK_REQ',2)
        Sleep(1000)

        EndTime = TimeStamp()       # 获取毫秒级时间戳
        Test , BidirV2LAvail1 = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_501','BIDIR_V2L_AVAIL', 0.0)
        Test , ACDCConversionState1 = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_501','ACDC_CONVERSION_STATE', 0.0)
        Test , EvsePlugLockState1 = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_421','EVSE_PLUG_LOCK_STATE', 0.0)
        TestResult11 = BidirV2LAvail1 == 0
        TestResult12 = ACDCConversionState1 == 0
        TestResult13 = EvsePlugLockState1 == 0
        TestResult1 = True if TestResult11 and TestResult12 and TestResult13 else False
        print(TestResult11,TestResult12,TestResult13)
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

        print(f"前置条件结果:{PreCondition}, 测试步骤1结果: {TestResult1}, 测试步骤2结果: {TestResult2},时间戳: {CursorPosition}")
        TestResult = True if PreCondition and TestResult1 and TestResult2 else False
        if TestResult == True:
            TestResultDisplay = '合格'
            print(TestResultDisplay)
        else:
            TestResultDisplay = '不合格'
            print(TestResultDisplay)

    if StartTestMethod8 == True:
        CloseAllCANMessage()
        InitDevice()
        Sleep(1000)
        STLA_CAN.DBC.ConfigureSetting('EVTECH_STLA-M_TS-VF-2', 'TS-NAV2L-05-8', RecordFileType.BLF, None)
        STLA_CAN.DBC.SetChannel('All', ['ALL'], RecordEnum.ON)
        STLA_CAN.DBC.RecordState(AcqEnum.Start)
        InitAllCANMessage()

        低压辅源.SCPI.Write(':SOUR1:VOLT 12.5;:SOUR1:CURR 3;:OUTP CH1,ON')
        低压辅源.SCPI.Write(':SOUR2:VOLT 5;:SOUR2:CURR 3;:OUTP CH2,ON')
        电阻控制板.Modbus.SetRegister(iID=1,Reg=3072,Data='150')
        信号发生器.SCPI.Write(':SOUR1:APPL:SQU 125,12.1,0,0;:SOUR1:FUNC:SQU:DCYC 53;:OUTP1 ON')
        Sleep(2000)

        STLA_CAN.DBC.SetSignal(1, 'DAT_TBMU_314', 'MIN_ALLOW_DISCHRG_VOLTAGE', 100)
        STLA_CAN.DBC.SetSignal(1,'DAT_E_VCU_448','OBC_EVSE_REQUEST',1)
        STLA_CAN.DBC.SetSignal(1,'DAT_E_VCU_448','CABLE_LOCK_REQ',1)
        Sleep(3000)

        交流源载一体机.Set.Basic(ACPwrModeEnum.LOAD, ACChannelEnum.SING, ACCouplingEnum.AC,0, ACPwrWorkModeEnum.CR)
        高压源载一体机.Set.Basic(DCPwrModeEnum.NORM, DCPwrWorkModeEnum.NONE)
        高压源载一体机.Set.Volt(dVolt=350)
        高压源载一体机.Out.Enable(eEnable.ON)
        Sleep(1000)

        STLA_CAN.DBC.SetSignal(1,'DAT_E_VCU_448','ACDC_CONVERSION_REQUEST',3)
        Sleep(2000)

        StartTime = TimeStamp()     # 获取毫秒级时间戳
        Test , ACDCConversionState0 = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_501','ACDC_CONVERSION_STATE', 0.0)
        PreCondition = ACDCConversionState0 == 4
        Sleep(2000)

        信号发生器.SCPI.Write(':SOUR1:APPL:SQU 600,12.1,0,0;:SOUR1:FUNC:SQU:DCYC 53;:OUTP1 ON')
        Sleep(1000)

        EndTime = TimeStamp()       # 获取毫秒级时间戳
        Test , BidirV2LAvail1 = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_501','BIDIR_V2L_AVAIL', 0.0)
        Test , ACDCConversionState1 = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_501','ACDC_CONVERSION_STATE', 0.0)
        Test , EvsePlugLockState1 = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_421','EVSE_PLUG_LOCK_STATE', 0.0)
        TestResult11 = BidirV2LAvail1 == 0
        TestResult12 = ACDCConversionState1 == 0
        TestResult1 = True if TestResult11 and TestResult12 else False
        print(TestResult11,TestResult12)
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

        print(f"前置条件结果:{PreCondition}, 测试步骤1结果: {TestResult1}, 测试步骤2结果: {TestResult2},时间戳: {CursorPosition}")
        TestResult = True if PreCondition and TestResult1 and TestResult2 else False
        if TestResult == True:
            TestResultDisplay = '合格'
            print(TestResultDisplay)
        else:
            TestResultDisplay = '不合格'
            print(TestResultDisplay)