from CommonFunction.FunctionClass_V2 import *
from UtilityClass.UtilityClass01_DeviceConnectInit import *
from CommonFunction.Common00_Fuction import *
from CommonFunction.Common04_SoftwareCommonFunction import STLA_M_EncapsulationClass

def run_test_with_different_configs():
    
    all_results = {
        'details': [],  # 存储每次测试的详细信息
        'summary': {    # 存储汇总信息
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'all_passed': False
        }
    }
    
    for config_vhl in [0, 1, 2, 3]:
        print(f"\n=== 开始测试 CONFIG_VHL = {config_vhl} ===")
        
        STLA_M_EncapsulationClass.InitDevice()
        STLA_M_EncapsulationClass.InitAllCANMessage()
        STLA_M_EncapsulationClass.TestCaseConfig(RecordStart=True, case_name="STLA-M-STEP2.5_PlantMode",case_id=f"CONFIG_VHL{config_vhl}")
        
        PreCondition = STLA_M_EncapsulationClass.EnterPlantModePreCondition(CONFIG_VHL=config_vhl)
        
        继电器控制板.Modbus.SetRegister(iID=1, Reg=3072, Data='8181')
        电阻控制板.Modbus.SetRegister(iID=1, Reg=3072, Data='220')
        STLA_CAN.DBC.SetSignal(1, get_message_for_signal('BMS_DC_RELAY_MES_EVSE_VOLTAGE'), 'BMS_DC_RELAY_MES_EVSE_VOLTAGE', 20)
        信号发生器.SCPI.Write(':SOUR1:APPL:SQU 1000,12.1,0,0;:SOUR1:FUNC:SQU:DCYC 50;:OUTP1 ON')
        交流源载一体机.Set.Basic(ACPwrModeEnum.SOUR, ACChannelEnum.EACH, ACCouplingEnum.AC, 0, ACPwrWorkModeEnum.CC)
        交流源载一体机.Set.Freq(dFreq=50)
        交流源载一体机.Set.Volt(dealListData([20.0, 20.0, 20.0]), dealListData([0.0, 0.0, 0.0]))
        交流源载一体机.Out.Enable(ACeEnable.ON)
        Sleep(17000)

        STLA_CAN.DBC.SendMessage(1, 'REQ_DIAG_ON_CAN_590', ['802', '54717', '0', '0'], 1, 100)  # 03 22 D5 BD
        AssignmentCode = 156

        STLA_M_EncapsulationClass.ExitPlantMode()
        STLA_M_EncapsulationClass.TestCaseConfig(RecordStart=False, case_name=f"STLA-M-STEP2.5_PlantMode_VHL{config_vhl}")
        STLA_M_EncapsulationClass.RCD_Exit_EcoMode()
        STLA_M_EncapsulationClass.CloseAllDevice()
        STLA_M_EncapsulationClass.CloseAllCANMessage()
        TestResult1 = STLA_M_EncapsulationClass.PlantModeScreenshot(faultcode=AssignmentCode, VerifyWhetherReportFault=False)
        TestResult = True if PreCondition and TestResult1 else False
        TestResultDisplay = '合格' if TestResult else '不合格'
        
        current_result = {
            'CONFIG_VHL': config_vhl,
            'PreCondition': PreCondition,
            'TestResult1': TestResult1,
            'FinalResult': TestResult,
            'DisplayResult': TestResultDisplay
        }
        all_results['details'].append(current_result)
        all_results['summary']['total_tests'] += 1
        if TestResult:
            all_results['summary']['passed'] += 1
        else:
            all_results['summary']['failed'] += 1
        print(f"CONFIG_VHL={config_vhl} 前置条件结果: {PreCondition}, 测试步骤1结果: {TestResult1}")
        print(f"CONFIG_VHL={config_vhl} 最终结果: {TestResultDisplay}")
    
    # 判断是否全部通过
    all_results['summary']['all_passed'] = (all_results['summary']['failed'] == 0)
    
    # 打印所有测试结果汇总
    print("\n=== 所有配置测试结果汇总 ===")
    for result in all_results['details']:
        print(f"CONFIG_VHL={result['CONFIG_VHL']}: "
              f"前置条件={result['PreCondition']}, "
              f"测试步骤1={result['TestResult1']}, "
              f"最终结果={result['DisplayResult']}")
    
    print("\n=== 最终汇总 ===")
    print(f"总测试次数: {all_results['summary']['total_tests']}")
    print(f"通过次数: {all_results['summary']['passed']}")
    print(f"失败次数: {all_results['summary']['failed']}")
    print(f"全部通过: {'是' if all_results['summary']['all_passed'] else '否'}")
    
    return all_results

if __name__ == '__main__':

    start_capture_prints()
    results = run_test_with_different_configs()
    if results['summary']['all_passed'] == True:
        TestResultDisplay = '合格'
        print(TestResultDisplay)
    else:
        TestResultDisplay = '不合格'
        print(TestResultDisplay)

    all_prints = stop_capture_prints()
    Log4NetWrapper.WriteToOutput_KeyInfo(TestResultDisplay, 
        f"\n"+
        f"1. Set CONFIG_VHL= 000 : Fitting,             after sending 0x590 according to the steps, the signal of IFB_Sample_Other_Resvd1=2. \n"+
        f"2. Set CONFIG_VHL= 001 : Plant,               after sending 0x590 according to the steps, the signal of IFB_Sample_Other_Resvd1=2. \n"+
        f"3. Set CONFIG_VHL= 010 : Check,               after sending 0x590 according to the steps, the signal of IFB_Sample_Other_Resvd1=2. \n"+
        f"4. Set CONFIG_VHL= 011 : Storage / Transport, after sending 0x590 according to the steps, the signal of IFB_Sample_Other_Resvd1=2. \n"+
        f"\n"+
        f"========================================================================="+
        f"\n"+
        f"{all_prints}"
    )









