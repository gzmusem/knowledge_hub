/**
 * 请求控制工具 - 防止重复请求
 */
class RequestControl {
  constructor() {
    this.cache = {};
    console.log('[RequestControl] 初始化简化版本');
  }

  // 执行请求但不进行锁定
  executeRequest(key, requestFunction) {
    console.log(`[RequestControl] 执行请求: ${key}`);
    return requestFunction().catch(error => {
      console.error(`[RequestControl] 请求失败: ${key}`, error);
      throw error;
    });
  }
  
  // 保持API兼容性的空方法
  lock() {}
  unlock() {}
  resetAllLocks() {}
}

// 导出实例
const requestControl = new RequestControl();
export default requestControl; 