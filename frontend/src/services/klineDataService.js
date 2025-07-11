import axios from 'axios';

// Use the correct backend API URL with port
const API_URL = 'http://localhost:5000/api';

/**
 * Service for fetching K-line chart data from the backend
 */
export default {
  /**
   * Get K-line data for a specific symbol and interval
   * @param {string} symbol - Trading pair symbol (e.g., BTC-USDT)
   * @param {string} interval - Time interval (e.g., 1m, 5m, 1h)
   * @param {string} startTime - Start time in ISO format or timestamp
   * @param {string} endTime - End time in ISO format or timestamp
   * @returns {Promise} - Promise with K-line data
   */
  getKlineData(symbol, interval, startTime = null, endTime = null, limit = null) {
    const params = {
      symbol,
      interval,
      ...(startTime && { start_time: startTime }),
      ...(endTime && { end_time: endTime }),
      ...(limit !== null && { limit })
    };
    
    return axios.get(`${API_URL}/kline-data`, { params });
  },
  
  /**
   * Get available trading pairs
   * @returns {Promise} - Promise with list of available symbols
   */
  getAvailableSymbols() {
    return axios.get(`${API_URL}/data-collection/symbols`);
  },
  
  /**
   * Get available time intervals
   * @returns {Promise} - Promise with list of available intervals
   */
  getAvailableIntervals() {
    return axios.get(`${API_URL}/data-collection/intervals`);
  },
  
  /**
   * Get market statistics for a specific symbol
   * @param {string} symbol - Trading pair symbol (e.g., BTC-USDT)
   * @returns {Promise} - Promise with market statistics
   */
  getMarketStats(symbol) {
    return axios.get(`${API_URL}/market-stats/${symbol}`);
  }
};