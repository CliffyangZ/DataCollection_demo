import axios from 'axios';

const API_URL = '/api';

export default {
  /**
   * 啟動數據收集任務
   * @param {Object} params - 收集參數
   * @returns {Promise} - API響應
   */
  startCollection(params) {
    return axios.post(`${API_URL}/data-collection/start`, params);
  },

  /**
   * 停止數據收集任務
   * @returns {Promise} - API響應
   */
  stopCollection() {
    return axios.post(`${API_URL}/data-collection/stop`);
  },

  /**
   * 獲取數據收集狀態
   * @returns {Promise} - API響應
   */
  getCollectionStatus() {
    return axios.get(`${API_URL}/data-collection/status`);
  },

  /**
   * 獲取收集歷史
   * @param {Object} params - 查詢參數
   * @returns {Promise} - API響應
   */
  getCollectionHistory(params) {
    return axios.get(`${API_URL}/data-collection/history`, { params });
  },

  /**
   * 獲取可用的交易對列表
   * @returns {Promise} - API響應
   */
  getAvailableSymbols() {
    return axios.get(`${API_URL}/data-collection/symbols`);
  },

  /**
   * 獲取可用的時間間隔
   * @returns {Promise} - API響應
   */
  getAvailableIntervals() {
    return axios.get(`${API_URL}/data-collection/intervals`);
  }
};